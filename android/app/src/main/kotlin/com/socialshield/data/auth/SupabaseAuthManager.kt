package com.socialshield.data.auth

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import com.socialshield.BuildConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import javax.inject.Inject
import javax.inject.Singleton

@Serializable
data class SupabaseUser(
    val id: String,
    val email: String,
    val displayName: String? = null,
    val role: String = "user"
)

@Serializable
data class SupabaseSession(
    val accessToken: String,
    val refreshToken: String? = null,
    val expiresIn: Long? = null,
    val user: SupabaseUser
)

sealed class AuthResult {
    data class Success(val user: SupabaseUser) : AuthResult()
    data class Error(val message: String) : AuthResult()
}

@Singleton
class SupabaseAuthManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val client: OkHttpClient,
    private val json: Json
) {
    private val tag = "SupabaseAuthManager"
    private val prefs: SharedPreferences = context.getSharedPreferences("supabase_auth_session", Context.MODE_PRIVATE)

    private val _currentUser = MutableStateFlow<SupabaseUser?>(null)
    val currentUserFlow: StateFlow<SupabaseUser?> = _currentUser.asStateFlow()

    val currentUser: SupabaseUser?
        get() = _currentUser.value

    val isUserLoggedIn: Boolean
        get() = _currentUser.value != null

    private val supabaseUrl: String = try {
        BuildConfig::class.java.getField("SUPABASE_URL").get(null) as? String
            ?: "https://your-project-ref.supabase.co/"
    } catch (e: Exception) {
        "https://your-project-ref.supabase.co/"
    }

    private val supabaseAnonKey: String = try {
        BuildConfig::class.java.getField("SUPABASE_ANON_KEY").get(null) as? String
            ?: "your-anon-key"
    } catch (e: Exception) {
        "your-anon-key"
    }

    init {
        restoreSession()
    }

    private fun restoreSession() {
        val userJson = prefs.getString("user_data", null)
        val token = prefs.getString("access_token", null)
        if (!userJson.isNullOrBlank() && !token.isNullOrBlank()) {
            try {
                val user = json.decodeFromString<SupabaseUser>(userJson)
                _currentUser.value = user
                Log.d(tag, "Restored Supabase user session: ${user.email} (ID: ${user.id})")
            } catch (e: Exception) {
                Log.e(tag, "Failed to restore session from prefs: ${e.message}")
                clearSession()
            }
        }
    }

    fun getAccessToken(): String {
        return prefs.getString("access_token", "dev_token") ?: "dev_token"
    }

    private fun saveSession(token: String, refreshToken: String?, user: SupabaseUser) {
        prefs.edit()
            .putString("access_token", token)
            .putString("refresh_token", refreshToken)
            .putString("user_data", json.encodeToString(SupabaseUser.serializer(), user))
            .apply()
        _currentUser.value = user
    }

    private fun clearSession() {
        prefs.edit().clear().apply()
        _currentUser.value = null
    }

    suspend fun signInWithEmail(email: String, pass: String): AuthResult = withContext(Dispatchers.IO) {
        if (isDemoOrUnconfigured()) {
            val cleanEmail = email.replace(Regex("[^a-zA-Z0-9]"), "_")
            val user = SupabaseUser(
                id = cleanEmail,
                email = email,
                displayName = email.substringBefore('@')
            )
            saveSession("demo_$cleanEmail", "demo_refresh", user)
            return@withContext AuthResult.Success(user)
        }

        try {
            val url = "${supabaseUrl.trimEnd('/')}/auth/v1/token?grant_type=password"
            val bodyJson = """{"email":"$email","password":"$pass"}"""
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", supabaseAnonKey)
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            client.newCall(request).execute().use { response ->
                val responseStr = response.body?.string() ?: ""
                if (response.isSuccessful) {
                    val root = json.parseToJsonElement(responseStr)
                    val obj = root as? kotlinx.serialization.json.JsonObject
                        ?: return@withContext AuthResult.Error("Unexpected response format")

                    val accessToken = obj["access_token"]?.toString()?.trim('"') ?: ""
                    val refreshToken = obj["refresh_token"]?.toString()?.trim('"')
                    val userObj = obj["user"] as? kotlinx.serialization.json.JsonObject

                    val userId = userObj?.get("id")?.toString()?.trim('"') ?: ""
                    val userEmail = userObj?.get("email")?.toString()?.trim('"') ?: email
                    val meta = userObj?.get("user_metadata") as? kotlinx.serialization.json.JsonObject
                    val name = meta?.get("full_name")?.toString()?.trim('"') ?: email.substringBefore('@')

                    val user = SupabaseUser(userId, userEmail, name)
                    saveSession(accessToken, refreshToken, user)
                    AuthResult.Success(user)
                } else {
                    val err = parseErrorMessage(responseStr)
                    AuthResult.Error(err)
                }
            }
        } catch (e: Exception) {
            Log.e(tag, "Supabase sign in failed: ${e.message}")
            AuthResult.Error(e.message ?: "Sign in failed")
        }
    }

    suspend fun signUpWithEmail(email: String, pass: String, fullName: String? = null): AuthResult = withContext(Dispatchers.IO) {
        if (isDemoOrUnconfigured()) {
            return@withContext signInWithEmail(email, pass)
        }

        try {
            val url = "${supabaseUrl.trimEnd('/')}/auth/v1/signup"
            val displayName = fullName ?: email.substringBefore('@')
            val bodyJson = """{"email":"$email","password":"$pass","data":{"full_name":"$displayName","name":"$displayName"}}"""
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", supabaseAnonKey)
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            client.newCall(request).execute().use { response ->
                val responseStr = response.body?.string() ?: ""
                if (response.isSuccessful) {
                    val root = json.parseToJsonElement(responseStr)
                    val obj = root as? kotlinx.serialization.json.JsonObject
                    val accessToken = obj?.get("access_token")?.toString()?.trim('"')
                    val userObj = obj?.get("user") as? kotlinx.serialization.json.JsonObject ?: obj

                    val userId = userObj?.get("id")?.toString()?.trim('"') ?: ""
                    val userEmail = userObj?.get("email")?.toString()?.trim('"') ?: email
                    val user = SupabaseUser(userId, userEmail, displayName)

                    if (!accessToken.isNullOrBlank()) {
                        saveSession(accessToken, obj?.get("refresh_token")?.toString()?.trim('"'), user)
                    }
                    AuthResult.Success(user)
                } else {
                    AuthResult.Error(parseErrorMessage(responseStr))
                }
            }
        } catch (e: Exception) {
            AuthResult.Error(e.message ?: "Sign up failed")
        }
    }

    suspend fun signInWithGoogle(idToken: String): AuthResult = withContext(Dispatchers.IO) {
        if (isDemoOrUnconfigured()) {
            val user = SupabaseUser("google_demo_user", "google_user@socialshield.ai", "Demo Google User")
            saveSession("demo_google_token", "demo_refresh", user)
            return@withContext AuthResult.Success(user)
        }

        try {
            val url = "${supabaseUrl.trimEnd('/')}/auth/v1/token?grant_type=id_token"
            val bodyJson = """{"provider":"google","id_token":"$idToken"}"""
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", supabaseAnonKey)
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            client.newCall(request).execute().use { response ->
                val responseStr = response.body?.string() ?: ""
                if (response.isSuccessful) {
                    val root = json.parseToJsonElement(responseStr)
                    val obj = root as? kotlinx.serialization.json.JsonObject
                    val accessToken = obj?.get("access_token")?.toString()?.trim('"') ?: ""
                    val userObj = obj?.get("user") as? kotlinx.serialization.json.JsonObject
                    val userId = userObj?.get("id")?.toString()?.trim('"') ?: ""
                    val userEmail = userObj?.get("email")?.toString()?.trim('"') ?: "google_user@socialshield.ai"
                    val user = SupabaseUser(userId, userEmail, userEmail.substringBefore('@'))
                    saveSession(accessToken, null, user)
                    AuthResult.Success(user)
                } else {
                    AuthResult.Error(parseErrorMessage(responseStr))
                }
            }
        } catch (e: Exception) {
            AuthResult.Error(e.message ?: "Google Sign-in failed")
        }
    }

    suspend fun resetPassword(email: String): AuthResult = withContext(Dispatchers.IO) {
        if (isDemoOrUnconfigured()) {
            return@withContext AuthResult.Success(SupabaseUser("demo", email, "Demo User"))
        }

        try {
            val url = "${supabaseUrl.trimEnd('/')}/auth/v1/recover"
            val bodyJson = """{"email":"$email"}"""
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", supabaseAnonKey)
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    AuthResult.Success(SupabaseUser("", email, ""))
                } else {
                    AuthResult.Error(parseErrorMessage(response.body?.string() ?: ""))
                }
            }
        } catch (e: Exception) {
            AuthResult.Error(e.message ?: "Password reset failed")
        }
    }

    fun signOut() {
        clearSession()
    }

    private fun isDemoOrUnconfigured(): Boolean {
        return supabaseUrl.contains("your-project") || supabaseUrl.contains("example") || supabaseAnonKey.contains("your-anon")
    }

    private fun parseErrorMessage(jsonStr: String): String {
        return try {
            val root = json.parseToJsonElement(jsonStr) as? kotlinx.serialization.json.JsonObject
            root?.get("error_description")?.toString()?.trim('"')
                ?: root?.get("msg")?.toString()?.trim('"')
                ?: root?.get("message")?.toString()?.trim('"')
                ?: "Authentication failed."
        } catch (e: Exception) {
            "Authentication failed."
        }
    }
}
