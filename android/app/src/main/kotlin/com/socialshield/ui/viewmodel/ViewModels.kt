// ─── Social Shield ViewModels (Supabase Auth & PostgreSQL Realtime Integration) ──
package com.socialshield.ui.viewmodel

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialshield.data.auth.AuthResult
import com.socialshield.data.auth.SupabaseAuthManager
import com.socialshield.data.repository.ApiResult
import com.socialshield.data.repository.ScanRepository
import com.socialshield.data.repository.PreferencesManager
import com.socialshield.domain.models.ScanHistoryItem
import com.socialshield.domain.models.ScanResult
import com.socialshield.utils.NotificationHelper
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

// ─── Auth ─────────────────────────────────────────────────────────────────────
data class AuthUiState(
    val isLoading: Boolean = false,
    val isLoggedIn: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authManager: SupabaseAuthManager
) : ViewModel() {
    private val _uiState = MutableStateFlow(AuthUiState(isLoggedIn = authManager.isUserLoggedIn))
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            authManager.currentUserFlow.collect { user ->
                _uiState.update { it.copy(isLoggedIn = user != null) }
            }
        }
    }

    fun signIn(email: String, password: String) {
        if (email.isBlank() || password.isBlank()) {
            _uiState.update { it.copy(error = "Email and password required") }
            return
        }
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            when (val res = authManager.signInWithEmail(email, password)) {
                is AuthResult.Success -> _uiState.update { it.copy(isLoading = false, isLoggedIn = true) }
                is AuthResult.Error -> _uiState.update { it.copy(isLoading = false, error = res.message) }
            }
        }
    }

    fun signUp(email: String, password: String) {
        if (email.isBlank() || password.isBlank()) {
            _uiState.update { it.copy(error = "Email and password required") }
            return
        }
        if (password.length < 6) {
            _uiState.update { it.copy(error = "Password must be at least 6 characters") }
            return
        }
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            when (val res = authManager.signUpWithEmail(email, password)) {
                is AuthResult.Success -> _uiState.update { it.copy(isLoading = false, isLoggedIn = true) }
                is AuthResult.Error -> _uiState.update { it.copy(isLoading = false, error = res.message) }
            }
        }
    }

    fun signInWithGoogle(idToken: String) {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            when (val res = authManager.signInWithGoogle(idToken)) {
                is AuthResult.Success -> _uiState.update { it.copy(isLoading = false, isLoggedIn = true) }
                is AuthResult.Error -> _uiState.update { it.copy(isLoading = false, error = res.message) }
            }
        }
    }

    fun signOut() {
        authManager.signOut()
        _uiState.update { AuthUiState(isLoggedIn = false) }
    }
}

// ─── Home ─────────────────────────────────────────────────────────────────────
data class HomeUiState(
    val userName: String = "",
    val trustScore: Int = 100,
    val totalScans: Int = 0,
    val fakeDetected: Int = 0,
    val suspiciousDetected: Int = 0,
    val recentScans: List<ScanHistoryItem> = emptyList()
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repo: ScanRepository,
    private val authManager: SupabaseAuthManager
) : ViewModel() {
    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            authManager.currentUserFlow.collect { user ->
                val name = user?.displayName ?: user?.email?.substringBefore('@') ?: "Shield User"
                _uiState.update { it.copy(userName = name) }
            }
        }

        // Listen to user stats in real-time from Supabase
        viewModelScope.launch {
            repo.getUserStatsFlow().collect { stats ->
                if (stats != null) {
                    _uiState.update {
                        it.copy(
                            trustScore = stats.trustScore,
                            totalScans = stats.totalScans,
                            fakeDetected = stats.fakeDetected,
                            suspiciousDetected = stats.suspiciousDetected
                        )
                    }
                }
            }
        }

        // Listen to recent history in real-time from Supabase
        viewModelScope.launch {
            repo.getHistoryFlow().collect { history ->
                _uiState.update {
                    it.copy(recentScans = history.take(5))
                }
            }
        }
    }
}

// ─── Scan ─────────────────────────────────────────────────────────────────────
data class ScanUiState(
    val isScanning: Boolean = false,
    val scanId: String? = null,
    val scanResult: ScanResult? = null,
    val error: String? = null
)

@HiltViewModel
class ScanViewModel @Inject constructor(
    private val repo: ScanRepository,
    @ApplicationContext private val context: Context
) : ViewModel() {
    private val _uiState = MutableStateFlow(ScanUiState())
    val uiState: StateFlow<ScanUiState> = _uiState.asStateFlow()

    fun scanImage(ctx: Context, uri: Uri) = scan { repo.scanImage(ctx, uri) }
    fun scanVideo(ctx: Context, uri: Uri) = scan { repo.scanVideo(ctx, uri) }
    fun scanAudio(ctx: Context, uri: Uri) = scan { repo.scanAudio(ctx, uri) }
    fun scanText(text: String) = scan { repo.scanText(text) }
    fun scanUrl(url: String) = scan { repo.scanUrl(url) }
    fun scanProfile(data: Map<String, Any>) = scan { repo.scanProfile(data) }

    fun resetScan() {
        _uiState.update { it.copy(isScanning = false, scanId = null, scanResult = null, error = null) }
    }

    private fun scan(block: suspend () -> ApiResult<ScanResult>) = viewModelScope.launch(Dispatchers.IO) {
        _uiState.update { it.copy(isScanning = true, error = null, scanId = null, scanResult = null) }
        when (val result = block()) {
            is ApiResult.Success -> {
                _uiState.update { it.copy(isScanning = false, scanId = result.data.scanId, scanResult = result.data) }
                
                // Trigger notification sound alert
                val verdict = result.data.verdict
                val title = "Scan Complete: $verdict"
                val message = when (verdict) {
                    "FAKE" -> "Warning: Deepfake or malicious content detected with high probability!"
                    "SUSPICIOUS" -> "Caution: Suspicious indicators found in scanned media."
                    else -> "Safe: No threat detected in scanned media."
                }
                NotificationHelper.showNotification(context, title, message)
            }
            is ApiResult.Error -> _uiState.update { it.copy(isScanning = false, error = result.message) }
        }
    }
}

// ─── Result ───────────────────────────────────────────────────────────────────
@HiltViewModel
class ResultViewModel @Inject constructor(private val repo: ScanRepository) : ViewModel() {
    private val _result = MutableStateFlow<ScanResult?>(null)
    val result: StateFlow<ScanResult?> = _result.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    fun loadResult(scanId: String) = viewModelScope.launch {
        _error.value = null
        when (val r = repo.getScanDetail(scanId)) {
            is ApiResult.Success -> _result.value = r.data
            is ApiResult.Error -> _error.value = r.message
        }
    }
}

// ─── History ─────────────────────────────────────────────────────────────────
data class HistoryUiState(
    val isLoading: Boolean = false,
    val scans: List<ScanHistoryItem> = emptyList(),
    val error: String? = null
)

@HiltViewModel
class HistoryViewModel @Inject constructor(private val repo: ScanRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(HistoryUiState())
    val uiState: StateFlow<HistoryUiState> = _uiState.asStateFlow()

    private val mediaTypeFilter = MutableStateFlow<String?>(null)
    private val searchQuery = MutableStateFlow("")

    init {
        _uiState.update { it.copy(isLoading = true) }
        viewModelScope.launch {
            combine(mediaTypeFilter, searchQuery, repo.getHistoryFlow(null)) { filter, query, history ->
                var filtered = if (filter != null) {
                    history.filter { it.mediaType == filter }
                } else {
                    history
                }
                if (query.isNotBlank()) {
                    filtered = filtered.filter { item ->
                        item.mediaType.contains(query, ignoreCase = true) ||
                        item.verdict.contains(query, ignoreCase = true) ||
                        item.scanId.contains(query, ignoreCase = true)
                    }
                }
                filtered
            }.collect { list ->
                _uiState.update { it.copy(isLoading = false, scans = list) }
            }
        }
    }

    fun loadHistory(mediaType: String?) {
        mediaTypeFilter.value = mediaType
    }

    fun setSearchQuery(query: String) {
        searchQuery.value = query
    }

    fun deleteScan(scanId: String) = viewModelScope.launch {
        repo.deleteScan(scanId)
    }
}

// ─── Settings ViewModel ────────────────────────────────────────────────────────
@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val preferencesManager: PreferencesManager,
    private val authManager: SupabaseAuthManager
) : ViewModel() {
    val currentUser = authManager.currentUserFlow.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = authManager.currentUser
    )

    fun signOut() {
        authManager.signOut()
    }
    val darkMode = preferencesManager.darkModeFlow.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = true
    )
    val localProcessing = preferencesManager.localProcessingFlow.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = false
    )
    val autoSaveScans = preferencesManager.autoSaveScansFlow.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = true
    )
    val threatAlerts = preferencesManager.threatAlertsFlow.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = true
    )

    fun setDarkMode(enabled: Boolean) = viewModelScope.launch {
        preferencesManager.setDarkMode(enabled)
    }

    fun setLocalProcessing(enabled: Boolean) = viewModelScope.launch {
        preferencesManager.setLocalProcessing(enabled)
    }

    fun setAutoSaveScans(enabled: Boolean) = viewModelScope.launch {
        preferencesManager.setAutoSaveScans(enabled)
    }

    fun setThreatAlerts(enabled: Boolean) = viewModelScope.launch {
        preferencesManager.setThreatAlerts(enabled)
    }
}
