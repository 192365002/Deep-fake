// ─── API Service ─────────────────────────────────────────────────────────────
package com.socialshield.data.api

import com.socialshield.domain.models.ScanResult
import com.socialshield.domain.models.ScanHistoryItem
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

import kotlinx.serialization.Serializable

interface SocialShieldApi {

    @Multipart
    @POST("api/v1/scan/image")
    suspend fun scanImage(
        @Part file: MultipartBody.Part,
        @Header("Authorization") token: String
    ): Response<ScanResult>

    @Multipart
    @POST("api/v1/scan/video")
    suspend fun scanVideo(
        @Part file: MultipartBody.Part,
        @Header("Authorization") token: String
    ): Response<ScanResult>

    @Multipart
    @POST("api/v1/scan/audio")
    suspend fun scanAudio(
        @Part file: MultipartBody.Part,
        @Header("Authorization") token: String
    ): Response<ScanResult>

    @POST("api/v1/scan/text")
    suspend fun scanText(
        @Body body: Map<String, String>,
        @Header("Authorization") token: String
    ): Response<ScanResult>

    @POST("api/v1/scan/url")
    suspend fun scanUrl(
        @Body body: Map<String, String>,
        @Header("Authorization") token: String
    ): Response<ScanResult>

    @POST("api/v1/scan/profile")
    suspend fun scanProfile(
        @Body body: Map<String, @JvmSuppressWildcards Any>,
        @Header("Authorization") token: String
    ): Response<ScanResult>

    @GET("api/v1/history")
    suspend fun getHistory(
        @Query("media_type") mediaType: String? = null,
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0,
        @Header("Authorization") token: String
    ): Response<HistoryResponse>

    @GET("api/v1/history/{scanId}")
    suspend fun getScanDetail(
        @Path("scanId") scanId: String,
        @Header("Authorization") token: String
    ): Response<ScanResult>

    @DELETE("api/v1/history/{scanId}")
    suspend fun deleteScan(
        @Path("scanId") scanId: String,
        @Header("Authorization") token: String
    ): Response<Unit>

    @GET("api/v1/stats")
    suspend fun getUserStats(
        @Header("Authorization") token: String
    ): Response<StatsResponse>
}

@Serializable
data class HistoryResponse(
    val items: List<ScanHistoryItem> = emptyList(),
    val count: Int = 0,
    val offset: Int = 0
)

@Serializable
data class StatsResponse(
    val totalScans: Int = 0,
    val fakeDetected: Int = 0,
    val suspiciousDetected: Int = 0,
    val safeDetected: Int = 0,
    val trustScore: Int = 100
)
