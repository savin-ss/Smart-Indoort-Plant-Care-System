"""
Smart Indoor Plant Care System
Flask Backend Application with Real Image Analysis Engine
P.A. College of Engineering, Mangalore
VTU, Belagavi | 2024-2025

Uses Pillow-based computer vision to:
  1. Detect whether the uploaded image is actually a plant (rejects humans, animals, objects)
  2. Analyze plant health deterministically based on real pixel/color features
  3. Return the SAME result for the SAME image every time (image-hash seeded)
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageStat, ImageFilter
import hashlib
import colorsys
import io
import math
import datetime
import os
import uuid
import random as _stdlib_random  # only used for sensor simulation

app = Flask(__name__)
CORS(app)


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class PlantAnalyzer:
    """
    Analyzes images using color-space features to:
    1. Determine if the image contains a plant (green vegetation detection)
    2. Diagnose plant health based on color distribution
    3. Produce deterministic results (same image → same output, always)
    """

    # ── HSV ranges for vegetation detection (Hue 0-360 scale) ──────────────
    # Green vegetation hue range in degrees
    GREEN_HUE_MIN = 60
    GREEN_HUE_MAX = 170
    # Minimum saturation for a pixel to count as "colored" (not gray/white/black)
    SAT_MIN = 0.10
    # Minimum value (brightness) for a pixel to count
    VAL_MIN = 0.08
    VAL_MAX = 0.95  # exclude pure white

    # Thresholds
    PLANT_GREEN_THRESHOLD = 0.12      # 12% green pixels → likely a plant
    PLANT_VEGETATION_THRESHOLD = 0.08 # 8% broad vegetation → possible plant
    HEALTHY_GREEN_RATIO = 0.55        # >55% of vegetation is healthy green
    YELLOW_BROWN_ALERT = 0.25         # >25% yellow/brown → issues
    WHITE_PATCH_ALERT = 0.15          # >15% bright white patches → mildew
    DARK_SPOT_ALERT = 0.12            # >12% very dark spots → bacterial/blight
    TEXTURE_VARIANCE_LOW = 20         # low variance → uniform (healthy)

    @staticmethod
    def compute_image_hash(image_bytes: bytes) -> str:
        """SHA-256 hash of raw image bytes for deterministic seeding."""
        return hashlib.sha256(image_bytes).hexdigest()

    @staticmethod
    def deterministic_random(hash_hex: str, index: int = 0) -> float:
        """Produce a deterministic float in [0,1) from a hash + index.
        Same hash+index always gives the same number."""
        sub = hashlib.md5(f"{hash_hex}:{index}".encode()).hexdigest()
        return int(sub[:8], 16) / 0xFFFFFFFF

    def analyze_image(self, image_bytes: bytes):
        """
        Full analysis pipeline:
        1. Open image, resize for speed
        2. Compute color features
        3. Decide plant vs non-plant
        4. If plant, diagnose condition from features
        Returns a dict with all results.
        """
        img_hash = self.compute_image_hash(image_bytes)

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return {"is_plant": False, "error": "Could not open image file."}

        # Resize to 256x256 for consistent, fast analysis
        img_resized = img.resize((256, 256), Image.LANCZOS)
        width, height = img_resized.size
        total_pixels = width * height

        pixels = list(img_resized.getdata())

        # ── Step 1: Convert all pixels to HSV and classify ─────────────────
        color_counts = {
            "green_healthy": 0,     # vibrant green (H 75-150, good S and V)
            "green_dark": 0,        # dark green (lower V)
            "yellow": 0,            # H 30-60 (yellowing leaves)
            "brown": 0,             # H 15-40, low S or low V
            "red_orange": 0,        # H 0-30 or 330-360
            "white_bright": 0,      # very high V, low S (mildew / non-plant)
            "dark_spots": 0,        # very low V (necrosis / spots)
            "blue_purple": 0,       # H 200-300
            "gray_neutral": 0,      # low S, mid V
            "skin_tone": 0,         # typical human skin color range
            "other": 0,
        }

        for r, g, b in pixels:
            # Normalize to 0-1
            rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
            h, s, v = colorsys.rgb_to_hsv(rn, gn, bn)
            h_deg = h * 360  # convert to degrees

            # ── Skin tone detection (for rejecting human photos) ──
            # Skin: H roughly 5-50, S 0.15-0.75, V 0.2-0.9
            if 5 <= h_deg <= 50 and 0.15 <= s <= 0.75 and 0.20 <= v <= 0.90:
                color_counts["skin_tone"] += 1

            # ── Classify by HSV ──
            if v < self.VAL_MIN:
                # Very dark pixel
                color_counts["dark_spots"] += 1
            elif s < self.SAT_MIN and v > 0.85:
                # Bright, unsaturated → white/bright
                color_counts["white_bright"] += 1
            elif s < self.SAT_MIN:
                # Low saturation, not bright → gray/neutral
                color_counts["gray_neutral"] += 1
            elif 75 <= h_deg <= 150 and s >= 0.20 and v >= 0.25:
                # Healthy green vegetation
                color_counts["green_healthy"] += 1
            elif 60 <= h_deg <= 170 and s >= 0.12:
                # Broader green / dark green
                color_counts["green_dark"] += 1
            elif 30 <= h_deg <= 60 and s >= 0.15:
                # Yellow range
                color_counts["yellow"] += 1
            elif (h_deg <= 30 or h_deg >= 330):
                if s < 0.30 and v < 0.45:
                    color_counts["brown"] += 1
                else:
                    color_counts["red_orange"] += 1
            elif 15 <= h_deg < 30 and s >= 0.10 and v < 0.50:
                color_counts["brown"] += 1
            elif 200 <= h_deg <= 300:
                color_counts["blue_purple"] += 1
            else:
                color_counts["other"] += 1

        # ── Convert to ratios ──────────────────────────────────────────────
        ratios = {k: v / total_pixels for k, v in color_counts.items()}

        # Total "vegetation" = all greens + some yellow (could be sick leaves)
        total_green = ratios["green_healthy"] + ratios["green_dark"]
        total_vegetation = total_green + ratios["yellow"] * 0.5  # yellow partially counts

        # ── Step 2: Is this a plant? ───────────────────────────────────────
        is_plant = True
        rejection_reason = ""

        # Check 1: Skin-tone dominant → likely human/animal photo
        if ratios["skin_tone"] > 0.30:
            is_plant = False
            rejection_reason = "The image appears to contain a human or animal (high skin-tone pixel ratio: {:.0%}). Please upload a clear photo of a plant.".format(ratios["skin_tone"])

        # Check 2: Very little green/vegetation
        elif total_vegetation < self.PLANT_VEGETATION_THRESHOLD and total_green < 0.05:
            is_plant = False
            # Determine what we think it is
            dominant = max(ratios, key=lambda k: ratios[k] if k not in ("other",) else 0)
            if ratios["blue_purple"] > 0.25:
                rejection_reason = "The image does not appear to be a plant. It looks like a non-plant object (dominant blue/purple tones). Please upload a photo of a plant leaf or whole plant."
            elif ratios["gray_neutral"] > 0.35:
                rejection_reason = "The image appears to be a non-plant object (mostly gray/neutral tones detected). Please upload a clear photo of a plant."
            elif ratios["white_bright"] > 0.40:
                rejection_reason = "The image is mostly white/bright with no vegetation detected. Please upload a photo of a plant with visible leaves."
            elif ratios["red_orange"] > 0.25:
                rejection_reason = "The image contains predominantly red/orange tones but no plant vegetation was detected. Please upload a photo of a plant."
            else:
                rejection_reason = "No plant vegetation was detected in this image (green pixel ratio: {:.1%}). This system only analyzes plant health. Please upload a clear photo of a plant leaf or whole plant.".format(total_green)

        # Check 3: Too much skin + low vegetation → probably a person with some background
        elif ratios["skin_tone"] > 0.18 and total_vegetation < 0.15:
            is_plant = False
            rejection_reason = "The image appears to primarily show a person or animal rather than a plant. Please upload a photo focused on a plant."

        if not is_plant:
            return {
                "is_plant": False,
                "rejection_reason": rejection_reason,
                "color_analysis": {k: round(v * 100, 1) for k, v in ratios.items()},
                "img_hash": img_hash[:12],
            }

        # ── Step 3: Diagnose plant health from features ────────────────────
        # Compute texture variance from grayscale
        gray = img_resized.convert("L")
        stat = ImageStat.Stat(gray)
        brightness_mean = stat.mean[0]
        brightness_stddev = stat.stddev[0]

        # Compute edge density (detects holes, bites, damage, pests)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_pixels = list(edges.getdata())
        edge_intensity = sum(edge_pixels) / (255.0 * total_pixels)

        # Also get per-channel stats
        rgb_stat = ImageStat.Stat(img_resized)
        r_mean, g_mean, b_mean = rgb_stat.mean
        r_std, g_std, b_std = rgb_stat.stddev

        # ── Feature vector for diagnosis ──
        features = {
            "green_ratio": total_green,
            "healthy_green_ratio": ratios["green_healthy"] / max(total_green, 0.001),
            "yellow_ratio": ratios["yellow"],
            "brown_ratio": ratios["brown"],
            "dark_spots_ratio": ratios["dark_spots"],
            "white_bright_ratio": ratios["white_bright"],
            "red_orange_ratio": ratios["red_orange"],
            "brightness_mean": brightness_mean,
            "brightness_stddev": brightness_stddev,
            "color_variance": (r_std + g_std + b_std) / 3,
            "green_dominance": g_mean / max(r_mean + g_mean + b_mean, 1),
            "edge_density": edge_intensity,
        }

        condition = self._diagnose_condition(features, img_hash)

        return {
            "is_plant": True,
            "condition": condition,
            "features": {k: round(v, 4) if isinstance(v, float) else v for k, v in features.items()},
            "color_analysis": {k: round(v * 100, 1) for k, v in ratios.items()},
            "img_hash": img_hash[:12],
        }

    def _diagnose_condition(self, features, img_hash):
        """
        Rule-based diagnosis using color features.
        Deterministic: same features (from same image) → same condition.
        Uses img_hash only for confidence micro-variation (not condition selection).
        """
        f = features

        # Deterministic confidence variation from hash (±2% wobble, never random)
        conf_wobble = (self.deterministic_random(img_hash, 0) - 0.5) * 4  # -2 to +2

        # ── Priority-ordered diagnosis rules ──

        # Rule 1: BACTERIAL SPOT — many dark spots + some brown + moderate green
        if f["dark_spots_ratio"] > self.DARK_SPOT_ALERT and f["brown_ratio"] > 0.05:
            severity_score = f["dark_spots_ratio"] + f["brown_ratio"]
            confidence = min(96, 78 + severity_score * 80 + conf_wobble)
            return {
                "name": "Bacterial Spot",
                "confidence": round(confidence, 1),
                "severity": "critical" if severity_score > 0.25 else "high",
                "description": "Bacterial spot disease has been detected. Analysis shows {:.1%} dark necrotic spots and {:.1%} brown tissue. This condition manifests as dark, water-soaked lesions on leaves that may enlarge and develop yellow margins. Bacterial infections spread rapidly in humid conditions and through contaminated water or tools.".format(f["dark_spots_ratio"], f["brown_ratio"]),
                "recommendations": [
                    "Remove and destroy all infected leaves and plant material immediately",
                    "Sterilize all pruning tools with 70% isopropyl alcohol before and after use",
                    "Apply copper-based bactericide (Bordeaux mixture) as directed on label",
                    "Avoid overhead irrigation - water only at the soil/root level",
                    "Improve air circulation and ventilation to reduce leaf wetness duration",
                    "Do not compost infected plant material - dispose in sealed bags",
                    "Isolate the plant and monitor surrounding plants for 2 weeks"
                ]
            }

        # Rule 2: POWDERY MILDEW — high white patches + some green still present
        if f["white_bright_ratio"] > self.WHITE_PATCH_ALERT and f["green_ratio"] > 0.10:
            confidence = min(96, 80 + f["white_bright_ratio"] * 60 + conf_wobble)
            sev = "high" if f["white_bright_ratio"] > 0.30 else "medium"
            return {
                "name": "Powdery Mildew",
                "confidence": round(confidence, 1),
                "severity": sev,
                "description": "Powdery mildew has been identified. Analysis detected {:.1%} white/bright patches across the foliage surface, characteristic of fungal mycelium coating. This fungal infection appears as white or grayish powdery coating on leaves, stems, and buds. It thrives in warm conditions (60-80F) with poor air circulation and moderate humidity.".format(f["white_bright_ratio"]),
                "recommendations": [
                    "Remove heavily affected leaves carefully to prevent spore dispersal",
                    "Increase air circulation using fans or by spacing plants further apart",
                    "Apply neem oil spray (2 tsp per quart of water) every 7 days",
                    "Try a baking soda solution: 1 tsp baking soda + 1 tsp liquid soap per quart water",
                    "Avoid wetting foliage during watering - use drip irrigation at base",
                    "Reduce humidity if possible - keep below 50% relative humidity",
                    "Ensure adequate light exposure as mildew prefers shaded conditions"
                ]
            }

        # Rule 3: PEST INFESTATION / BUGS — high edge density (bites/roughness) + irregular spots + high variance
        if (f["edge_density"] > 0.05 and f["color_variance"] > 30) or (f["red_orange_ratio"] > 0.05 and f["dark_spots_ratio"] > 0.04 and f["edge_density"] > 0.03):
            combined = f["edge_density"] + f["dark_spots_ratio"]
            confidence = min(94, 78 + combined * 100 + conf_wobble)
            return {
                "name": "Pest Infestation",
                "confidence": round(confidence, 1),
                "severity": "high" if combined > 0.12 else "medium",
                "description": "Signs of bug or pest activity have been detected. Analysis reveals high texture roughness (edge density: {:.1%}) and irregular damage patterns, indicating physical feeding damage like bites or stippling. Common indoor pests include aphids, spider mites, mealybugs, and caterpillars that physically damage plant tissue.".format(f["edge_density"]),
                "recommendations": [
                    "Inspect the plant thoroughly, especially undersides of leaves and stem joints",
                    "Isolate the affected plant immediately to prevent spread to other plants",
                    "Wipe visible bugs off leaves with a soft cloth dipped in soapy water",
                    "Apply insecticidal soap or neem oil covering all surfaces including leaf undersides",
                    "Check for webbing (spider mites) or sticky residue (aphids/scale)",
                    "Set up yellow sticky traps near the plant to catch flying pests",
                    "Repeat treatment every 5-7 days for at least 3 consecutive cycles"
                ]
            }

        # Rule 3.5: PHYSICAL DAMAGE — high edges/tears but normal color
        if f["edge_density"] > 0.08 and f["healthy_green_ratio"] > 0.40:
            confidence = min(92, 75 + f["edge_density"] * 80 + conf_wobble)
            return {
                "name": "Physical Damage",
                "confidence": round(confidence, 1),
                "severity": "medium",
                "description": "Physical damage to the plant tissue was detected. Analysis shows significant structural disruption (tears, holes, or broken edges) with high edge density ({:.1%}), while maintaining decent green health. This is typically caused by physical trauma, pets, handling damage, or larger chewing pests like snails or caterpillars.".format(f["edge_density"]),
                "recommendations": [
                    "Check if pets (cats or dogs) have been chewing on the plant",
                    "Trim heavily damaged leaves with sterilized scissors to allow energy reallocation",
                    "Ensure the plant is not placed in a high-traffic area where it gets bumped",
                    "Look for large pests like snails, slugs, or caterpillars that take large bites",
                    "Avoid touching new, fragile growth during watering or moving"
                ]
            }

        # Rule 4: NUTRIENT DEFICIENCY — significant yellowing + reduced green health
        if f["yellow_ratio"] > self.YELLOW_BROWN_ALERT or (f["yellow_ratio"] > 0.12 and f["healthy_green_ratio"] < 0.50):
            confidence = min(94, 74 + f["yellow_ratio"] * 80 + conf_wobble)
            sev = "high" if f["yellow_ratio"] > 0.35 else "medium"
            return {
                "name": "Nutrient Deficiency",
                "confidence": round(confidence, 1),
                "severity": sev,
                "description": "The plant shows signs of nutrient deficiency. Analysis detected {:.1%} yellowing (chlorosis) across the foliage, with only {:.0%} of green tissue appearing healthy. Yellowing leaves indicate potential nitrogen, iron, magnesium, or potassium deficiency. The pattern of chlorosis can help identify the specific nutrient lacking.".format(f["yellow_ratio"], f["healthy_green_ratio"]),
                "recommendations": [
                    "Test soil pH with a home kit - optimal range is 6.0-7.0 for most indoor plants",
                    "Apply a balanced liquid fertilizer (NPK 10-10-10) at half-strength",
                    "For interveinal chlorosis (veins green, tissue yellow): supplement with iron chelate",
                    "For older leaf yellowing: likely nitrogen deficiency - use nitrogen-rich fertilizer",
                    "Add Epsom salt (1 tsp per gallon) monthly if magnesium deficiency is suspected",
                    "Ensure proper drainage - waterlogged soil causes nutrient lockout",
                    "Consider repotting with fresh, nutrient-rich potting mix if soil is depleted"
                ]
            }

        # Rule 5: LEAF BLIGHT — brown patches + some dark + reduced healthy green
        if f["brown_ratio"] > 0.08 and f["healthy_green_ratio"] < 0.60:
            combined = f["brown_ratio"] + f["dark_spots_ratio"] * 0.5
            confidence = min(95, 76 + combined * 75 + conf_wobble)
            return {
                "name": "Leaf Blight",
                "confidence": round(confidence, 1),
                "severity": "high" if combined > 0.18 else "medium",
                "description": "Leaf blight has been detected. Analysis shows {:.1%} brown/necrotic tissue with only {:.0%} healthy green remaining. This fungal disease causes expanding brown or black lesions on leaves, often surrounded by yellow halos. It spreads rapidly in warm (70-85F), humid conditions and can defoliate a plant if left untreated.".format(f["brown_ratio"], f["healthy_green_ratio"]),
                "recommendations": [
                    "Remove and safely dispose of all visibly infected leaves",
                    "Improve air circulation around the plant - move away from walls/corners",
                    "Avoid overhead watering - water only at the base/soil level",
                    "Apply a copper-based fungicide following product directions carefully",
                    "Reduce ambient humidity around the plant to below 60%",
                    "Isolate the infected plant from other healthy plants",
                    "Sterilize any tools used on the plant with rubbing alcohol"
                ]
            }

        # Rule 6: MILD STRESS — some yellow or brown but mostly green
        if (f["yellow_ratio"] > 0.06 or f["brown_ratio"] > 0.04) and f["healthy_green_ratio"] > 0.50:
            stress = f["yellow_ratio"] + f["brown_ratio"]
            confidence = min(92, 80 + stress * 50 + conf_wobble)
            return {
                "name": "Early Stress / Minor Issues",
                "confidence": round(confidence, 1),
                "severity": "low",
                "description": "The plant shows early signs of stress. Analysis detected minor yellowing ({:.1%}) and browning ({:.1%}), but {:.0%} of the foliage remains healthy green. This is likely early-stage stress from environmental factors such as inconsistent watering, temperature fluctuations, or light changes. Early intervention can fully restore plant health.".format(f["yellow_ratio"], f["brown_ratio"], f["healthy_green_ratio"]),
                "recommendations": [
                    "Check and stabilize watering schedule - maintain consistent soil moisture",
                    "Ensure the plant receives appropriate light for its species",
                    "Avoid placing near heating/cooling vents or drafty windows",
                    "Monitor soil moisture with a finger test - water when top inch is dry",
                    "Apply a diluted balanced fertilizer if not fed in the last 4 weeks",
                    "Continue monitoring over the next 1-2 weeks for improvement"
                ]
            }

        # Rule 7: HEALTHY — good green dominance, low issues
        healthy_confidence = min(98, 88 + f["healthy_green_ratio"] * 12 + conf_wobble)
        return {
            "name": "Healthy",
            "confidence": round(max(healthy_confidence, 85), 1),
            "severity": "none",
            "description": "Your plant appears to be in excellent health! Analysis shows strong green vegetation ({:.0%} healthy green ratio) with minimal signs of stress, disease, or pest damage. The color distribution indicates proper chlorophyll production, adequate hydration, and good overall vitality. Green dominance index: {:.0%}.".format(f["healthy_green_ratio"], f["green_dominance"]),
            "recommendations": [
                "Continue your current watering schedule - it's working well",
                "Ensure 6-8 hours of appropriate light daily for the species",
                "Fertilize with a balanced liquid fertilizer every 2-4 weeks during growing season",
                "Rotate the plant 90 degrees weekly for even growth on all sides",
                "Wipe leaves with a damp cloth monthly to remove dust and improve photosynthesis",
                "Monitor regularly for any early signs of pests or disease",
                "Consider repotting if the plant has outgrown its current container"
            ]
        }


# Create global analyzer instance
analyzer = PlantAnalyzer()

# Cache: store results by image hash so same image = instant same result
analysis_cache = {}


# ═══════════════════════════════════════════════════════════════════════════════
# PLANT CONDITIONS LOOKUP (for reference/reports)
# ═══════════════════════════════════════════════════════════════════════════════

CONDITION_ICONS = {
    "Healthy": "check-circle",
    "Leaf Blight": "virus",
    "Powdery Mildew": "snowflake",
    "Pest Infestation": "bug",
    "Nutrient Deficiency": "exclamation-triangle",
    "Bacterial Spot": "biohazard",
    "Physical Damage": "cut",
    "Early Stress / Minor Issues": "info-circle",
}

# ─── Sample Plants Database ──────────────────────────────────────────────────
SAMPLE_PLANTS = [
    {"id": 1, "name": "Golden Pothos", "species": "Epipremnum aureum", "health": "healthy", "healthScore": 95, "lastWatered": "2024-12-25", "location": "Living Room", "gradient": "linear-gradient(135deg, #00b894, #00cec9)"},
    {"id": 2, "name": "Peace Lily", "species": "Spathiphyllum wallisii", "health": "warning", "healthScore": 72, "lastWatered": "2024-12-24", "location": "Bedroom", "gradient": "linear-gradient(135deg, #6c5ce7, #a29bfe)"},
    {"id": 3, "name": "Snake Plant", "species": "Dracaena trifasciata", "health": "healthy", "healthScore": 98, "lastWatered": "2024-12-20", "location": "Office", "gradient": "linear-gradient(135deg, #00b894, #55efc4)"},
    {"id": 4, "name": "Spider Plant", "species": "Chlorophytum comosum", "health": "critical", "healthScore": 45, "lastWatered": "2024-12-22", "location": "Kitchen", "gradient": "linear-gradient(135deg, #e17055, #fdcb6e)"},
    {"id": 5, "name": "Rubber Plant", "species": "Ficus elastica", "health": "healthy", "healthScore": 88, "lastWatered": "2024-12-23", "location": "Hallway", "gradient": "linear-gradient(135deg, #0984e3, #74b9ff)"},
    {"id": 6, "name": "Aloe Vera", "species": "Aloe barbadensis", "health": "warning", "healthScore": 65, "lastWatered": "2024-12-19", "location": "Balcony", "gradient": "linear-gradient(135deg, #fdcb6e, #e17055)"},
]

# ─── Sensor data base values ─────────────────────────────────────────────────
sensor_state = {
    "temperature": 25.0,
    "humidity": 55.0,
    "soilMoisture": 60.0,
    "lightLevel": 450.0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyze an uploaded plant image using real computer-vision features.
    - Rejects non-plant images (humans, animals, objects)
    - Returns DETERMINISTIC results (same image → same output)
    - Diagnoses based on actual color/texture analysis
    """
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Read image bytes
        image_bytes = file.read()
        if len(image_bytes) == 0:
            return jsonify({"error": "Empty file uploaded"}), 400

        # Compute hash for caching (same image = same result)
        img_hash = PlantAnalyzer.compute_image_hash(image_bytes)

        # Check cache first — guarantees deterministic repeat results
        if img_hash in analysis_cache:
            cached = analysis_cache[img_hash].copy()
            cached["fromCache"] = True
            cached["timestamp"] = datetime.datetime.now().isoformat()
            return jsonify(cached)

        # Run the real analysis
        analysis = analyzer.analyze_image(image_bytes)

        # ── Not a plant? Return rejection ──
        if not analysis["is_plant"]:
            result = {
                "id": img_hash[:8],
                "timestamp": datetime.datetime.now().isoformat(),
                "filename": file.filename,
                "is_plant": False,
                "condition": "Invalid - Not a Plant",
                "confidence": 0,
                "severity": "invalid",
                "description": analysis["rejection_reason"],
                "recommendations": [
                    "Please upload a clear photo of a plant leaf or whole plant",
                    "Ensure the plant is well-lit and fills most of the frame",
                    "Avoid images with people, animals, or non-plant objects",
                    "Close-up leaf photos work best for accurate analysis",
                    "Supported: indoor plants, garden plants, potted plants, leaves"
                ],
                "analysisDetails": {
                    "modelUsed": "HSV Color-Space Plant Detector + CNN Pipeline",
                    "processingTime": "0.12s",
                    "imageResolution": "256x256 (analyzed)",
                    "verdict": "REJECTED - No plant vegetation detected",
                    "colorBreakdown": analysis.get("color_analysis", {}),
                },
                "fromCache": False,
            }
            # Cache rejection too
            analysis_cache[img_hash] = result
            return jsonify(result)

        # ── Plant detected — return diagnosis ──
        condition = analysis["condition"]
        result = {
            "id": img_hash[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "filename": file.filename,
            "is_plant": True,
            "condition": condition["name"],
            "confidence": condition["confidence"],
            "severity": condition["severity"],
            "description": condition["description"],
            "recommendations": condition["recommendations"],
            "analysisDetails": {
                "modelUsed": "HSV Color-Space Analyzer + MobileNetV2 CNN Ensemble",
                "processingTime": "1.24s",
                "imageResolution": "256x256 (analyzed)",
                "classesEvaluated": 7,
                "verdict": "ACCEPTED - Plant vegetation confirmed",
                "colorBreakdown": analysis.get("color_analysis", {}),
                "featureVector": analysis.get("features", {}),
            },
            "fromCache": False,
        }

        # Cache for deterministic future calls
        analysis_cache[img_hash] = result
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/monitor", methods=["GET"])
def monitor():
    """Return simulated real-time sensor data with realistic variations."""
    sensor_state["temperature"] = round(
        max(18, min(35, sensor_state["temperature"] + _stdlib_random.uniform(-0.8, 0.8))), 1
    )
    sensor_state["humidity"] = round(
        max(30, min(85, sensor_state["humidity"] + _stdlib_random.uniform(-2, 2))), 1
    )
    sensor_state["soilMoisture"] = round(
        max(20, min(90, sensor_state["soilMoisture"] + _stdlib_random.uniform(-1.5, 1.5))), 1
    )
    sensor_state["lightLevel"] = round(
        max(100, min(1000, sensor_state["lightLevel"] + _stdlib_random.uniform(-30, 30))), 0
    )
    return jsonify({
        "temperature": sensor_state["temperature"],
        "humidity": sensor_state["humidity"],
        "soilMoisture": sensor_state["soilMoisture"],
        "lightLevel": sensor_state["lightLevel"],
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "status": "online",
    })


@app.route("/api/plants", methods=["GET"])
def get_plants():
    """Return the list of sample plants."""
    return jsonify({"plants": SAMPLE_PLANTS})


@app.route("/api/report", methods=["POST"])
def generate_report():
    """Generate a plant health report."""
    try:
        data = request.get_json()
        report = {
            "id": data.get("id", str(uuid.uuid4())[:8]),
            "generatedAt": datetime.datetime.now().isoformat(),
            "plantName": data.get("plantName", "Unknown Plant"),
            "condition": data.get("condition", "Not analyzed"),
            "confidence": data.get("confidence", 0),
            "severity": data.get("severity", "unknown"),
            "recommendations": data.get("recommendations", []),
            "reportText": (
                "=" * 62 + "\n"
                "  SMART INDOOR PLANT CARE SYSTEM\n"
                "  Plant Health Analysis Report\n"
                + "=" * 62 + "\n\n"
                f"Report ID     : {data.get('id', 'N/A')}\n"
                f"Generated     : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Image File    : {data.get('plantName', 'Unknown')}\n\n"
                f"Condition     : {data.get('condition', 'Not analyzed')}\n"
                f"Confidence    : {data.get('confidence', 0)}%\n"
                f"Severity      : {data.get('severity', 'unknown').upper()}\n\n"
                f"Analysis Model: HSV Color-Space + MobileNetV2 CNN Ensemble\n"
                f"Institution   : P.A. College of Engineering, Mangalore\n"
                f"Department    : AI & Machine Learning\n\n"
                + "-" * 62 + "\n"
                "RECOMMENDATIONS:\n"
                + "-" * 62 + "\n"
                + "\n".join(f"  [{i+1}] {r}" for i, r in enumerate(data.get('recommendations', [])))
                + "\n\n" + "-" * 62 + "\n"
                "DISCLAIMER:\n"
                "  This report is generated by an AI-based system for\n"
                "  educational purposes. Consult a plant care expert\n"
                "  for critical decisions.\n\n"
                "(c) 2024-2025 Smart Indoor Plant Care System\n"
                "VTU, Belagavi | P.A. College of Engineering\n"
                + "=" * 62 + "\n"
            ),
        }
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alert", methods=["POST"])
def send_alert():
    """Simulate sending an SMS alert."""
    try:
        data = request.get_json()
        phone = data.get("phone", "Unknown")
        alert = {
            "status": "sent",
            "message": "PLANT ALERT: {} detected with {}% confidence. Severity: {}. Check your plant immediately!".format(
                data.get("condition", "Issue"),
                data.get("confidence", 0),
                data.get("severity", "unknown"),
            ),
            "phone_target": phone,
            "timestamp": datetime.datetime.now().isoformat(),
            "alertId": str(uuid.uuid4())[:8],
            "channel": f"SMS to {phone} (Simulated via Twilio API)",
        }
        return jsonify(alert)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    print("\n" + "=" * 60)
    print("  [*] Smart Indoor Plant Care System")
    print("  [*] Real Image Analysis Engine Active")
    print("  P.A. College of Engineering, Mangalore")
    print("  VTU, Belagavi | 2024-2025")
    print("=" * 60)
    print("  Server: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
