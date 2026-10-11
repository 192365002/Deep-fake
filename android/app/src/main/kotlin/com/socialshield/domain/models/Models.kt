// ─── Domain Models ───────────────────────────────────────────────────────────
package com.socialshield.domain.models

import kotlinx.serialization.Serializable
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import kotlinx.serialization.descriptors.*
import kotlinx.serialization.encoding.*

enum class ScanType(val displayName: String, val infoText: String) {
    IMAGE("Scan Image", "Upload a photo to detect AI-generated or manipulated faces using our EfficientNet deep learning model with Grad-CAM visualization."),
    VIDEO("Scan Video", "Upload a video to analyze frames for deepfake manipulation using temporal consistency analysis and blink pattern detection."),
    AUDIO("Scan Audio", "Upload an audio file to detect AI voice cloning or synthetic speech using mel-spectrogram CNN analysis."),
    TEXT("Scan Text", "Paste any text message to detect phishing, scam, or fraud intent using our NLP model trained on real-world fraud datasets."),
    URL("Scan URL", "Enter a URL to check against Google Safe Browsing, VirusTotal, and heuristic phishing pattern analysis."),
    PROFILE("Scan Profile", "Enter social media profile data to identify bot accounts, fake profiles, and suspicious behavior patterns.")
}

@Serializable
data class ScanResult(
    val scanId: String,
    val userId: String,
    val mediaType: String,
    val verdict: String,
    val confidence: Float,
    val fakeProbability: Float,
    val realProbability: Float,
    val riskLevel: String,
    val explanations: List<String>,
    val recommendations: List<String> = emptyList(),
    val heatmapBase64: String? = null,
    val metadata: Map<String, @Serializable(with = AnySerializer::class) Any?>? = null,
    val timestamp: String
)

@Serializable
data class ScanHistoryItem(
    val scanId: String = "",
    val mediaType: String = "IMAGE",
    val verdict: String = "SAFE",
    val confidence: Float = 100f,
    val timestamp: String = ""
)

// Serializer for Any type

object AnySerializer : KSerializer<Any?> {
    override val descriptor = buildClassSerialDescriptor("Any")
    override fun serialize(encoder: Encoder, value: Any?) {
        val jsonEncoder = encoder as? JsonEncoder ?: return
        jsonEncoder.encodeJsonElement(JsonNull)
    }
    override fun deserialize(decoder: Decoder): Any? {
        val jsonDecoder = decoder as? JsonDecoder ?: return null
        return when (val element = jsonDecoder.decodeJsonElement()) {
            is JsonNull -> null
            is JsonPrimitive -> when {
                element.isString -> element.content
                element.booleanOrNull != null -> element.boolean
                element.intOrNull != null -> element.int
                element.doubleOrNull != null -> element.double
                else -> element.content
            }
            else -> element.toString()
        }
    }
}
