package com.socialshield.data.repository

import android.content.Context
import android.net.Uri
import com.socialshield.data.api.SocialShieldApi
import com.socialshield.data.api.StatsResponse
import com.socialshield.data.auth.SupabaseAuthManager
import com.socialshield.domain.models.ScanResult
import com.socialshield.domain.models.ScanHistoryItem
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton

sealed class ApiResult<T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error<T>(val message: String) : ApiResult<T>()
}

@Singleton
class ScanRepository @Inject constructor(
    private val api: SocialShieldApi,
    private val authManager: SupabaseAuthManager
) {
    private var cachedResult: ScanResult? = null
    private val refreshTrigger = MutableSharedFlow<Unit>(replay = 1).apply { tryEmit(Unit) }

    private fun getAuthToken(): String {
        val token = authManager.getAccessToken()
        return "Bearer $token"
    }

    private fun uriToFile(context: Context, uri: Uri, prefix: String, suffix: String): File {
        val file = File.createTempFile(prefix, suffix, context.cacheDir)
        context.contentResolver.openInputStream(uri)?.use { input ->
            FileOutputStream(file).use { output -> input.copyTo(output) }
        }
        return file
    }

    /**
     * Realtime flow emitting user statistics from Supabase Backend.
     * Periodically updates and immediately refreshes on new scans.
     */
    fun getUserStatsFlow(): Flow<StatsResponse?> = flow {
        while (true) {
            val user = authManager.currentUser
            if (user == null) {
                emit(StatsResponse(0, 0, 0, 100))
            } else {
                try {
                    val token = getAuthToken()
                    val response = api.getUserStats(token)
                    if (response.isSuccessful && response.body() != null) {
                        emit(response.body())
                    } else {
                        emit(StatsResponse(0, 0, 0, 100))
                    }
                } catch (e: Exception) {
                    emit(StatsResponse(0, 0, 0, 100))
                }
            }
            delay(5000) // Poll every 5 seconds for live multi-device synchronization
        }
    }.flowOn(Dispatchers.IO)

    /**
     * Realtime flow emitting scan history items from Supabase Backend.
     * Synchronizes bidirectional additions and deletions across Android and Web.
     */
    fun getHistoryFlow(mediaType: String? = null): Flow<List<ScanHistoryItem>> = flow {
        while (true) {
            val user = authManager.currentUser
            if (user == null) {
                emit(emptyList())
            } else {
                try {
                    val token = getAuthToken()
                    val response = api.getHistory(mediaType = mediaType, limit = 50, offset = 0, token = token)
                    if (response.isSuccessful && response.body() != null) {
                        emit(response.body()!!.items)
                    }
                } catch (e: Exception) {
                    // Retain current state on network hiccups
                }
            }
            delay(5000) // Multi-device synchronization refresh cadence
        }
    }.flowOn(Dispatchers.IO)

    suspend fun scanImage(context: Context, uri: Uri): ApiResult<ScanResult> = runCatching {
        val token = getAuthToken()
        val file = uriToFile(context, uri, "img_", ".jpg")
        val part = MultipartBody.Part.createFormData("file", file.name, file.asRequestBody("image/*".toMediaTypeOrNull()))
        val response = api.scanImage(part, token)
        file.delete()
        val body = response.body()
        if (response.isSuccessful && body != null) {
            cachedResult = body
            refreshTrigger.emit(Unit)
            ApiResult.Success(body)
        } else {
            ApiResult.Error("Server error: ${response.code()} or empty response")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun scanVideo(context: Context, uri: Uri): ApiResult<ScanResult> = runCatching {
        val token = getAuthToken()
        val file = uriToFile(context, uri, "vid_", ".mp4")
        val part = MultipartBody.Part.createFormData("file", file.name, file.asRequestBody("video/*".toMediaTypeOrNull()))
        val response = api.scanVideo(part, token)
        file.delete()
        val body = response.body()
        if (response.isSuccessful && body != null) {
            cachedResult = body
            refreshTrigger.emit(Unit)
            ApiResult.Success(body)
        } else {
            ApiResult.Error("Server error: ${response.code()} or empty response")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun scanAudio(context: Context, uri: Uri): ApiResult<ScanResult> = runCatching {
        val token = getAuthToken()
        val file = uriToFile(context, uri, "aud_", ".mp3")
        val part = MultipartBody.Part.createFormData("file", file.name, file.asRequestBody("audio/*".toMediaTypeOrNull()))
        val response = api.scanAudio(part, token)
        file.delete()
        val body = response.body()
        if (response.isSuccessful && body != null) {
            cachedResult = body
            refreshTrigger.emit(Unit)
            ApiResult.Success(body)
        } else {
            ApiResult.Error("Server error: ${response.code()} or empty response")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun scanText(text: String): ApiResult<ScanResult> = runCatching {
        val token = getAuthToken()
        val response = api.scanText(mapOf("text" to text), token)
        val body = response.body()
        if (response.isSuccessful && body != null) {
            cachedResult = body
            refreshTrigger.emit(Unit)
            ApiResult.Success(body)
        } else {
            ApiResult.Error("Server error: ${response.code()} or empty response")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun scanUrl(url: String): ApiResult<ScanResult> = runCatching {
        val token = getAuthToken()
        val response = api.scanUrl(mapOf("url" to url), token)
        val body = response.body()
        if (response.isSuccessful && body != null) {
            cachedResult = body
            refreshTrigger.emit(Unit)
            ApiResult.Success(body)
        } else {
            ApiResult.Error("Server error: ${response.code()} or empty response")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun scanProfile(data: Map<String, Any>): ApiResult<ScanResult> = runCatching {
        val token = getAuthToken()
        val response = api.scanProfile(data, token)
        val body = response.body()
        if (response.isSuccessful && body != null) {
            cachedResult = body
            refreshTrigger.emit(Unit)
            ApiResult.Success(body)
        } else {
            ApiResult.Error("Server error: ${response.code()} or empty response")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun getHistory(mediaType: String? = null): ApiResult<List<ScanHistoryItem>> = runCatching {
        val token = getAuthToken()
        val response = api.getHistory(mediaType, token = token)
        val body = response.body()
        if (response.isSuccessful && body != null) {
            ApiResult.Success(body.items)
        } else {
            ApiResult.Error("Server error: ${response.code()} or empty response")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun getScanDetail(scanId: String): ApiResult<ScanResult> = runCatching {
        if (cachedResult?.scanId == scanId) {
            return@runCatching ApiResult.Success(cachedResult!!)
        }
        val token = getAuthToken()
        val response = api.getScanDetail(scanId, token)
        val body = response.body()
        if (response.isSuccessful && body != null) {
            ApiResult.Success(body)
        } else {
            ApiResult.Error("Scan details not found")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun deleteScan(scanId: String): ApiResult<Unit> = runCatching {
        val token = getAuthToken()
        val response = api.deleteScan(scanId, token)
        if (response.isSuccessful) {
            refreshTrigger.emit(Unit)
            ApiResult.Success(Unit)
        } else {
            ApiResult.Error("Failed to delete scan: HTTP ${response.code()}")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }

    suspend fun getUserStats(): ApiResult<StatsResponse> = runCatching {
        val token = getAuthToken()
        val response = api.getUserStats(token)
        val body = response.body()
        if (response.isSuccessful && body != null) {
            ApiResult.Success(body)
        } else {
            ApiResult.Error("Server error or empty stats")
        }
    }.getOrElse { ApiResult.Error(it.message ?: "Unknown error") }
}
