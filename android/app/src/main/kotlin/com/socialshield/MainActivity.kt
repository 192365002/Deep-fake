package com.socialshield

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.*
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.socialshield.data.auth.SupabaseAuthManager
import com.socialshield.domain.models.ScanType
import com.socialshield.ui.screens.*
import com.socialshield.ui.theme.*
import com.socialshield.data.repository.PreferencesManager
import android.os.Build
import com.socialshield.utils.NotificationHelper
import androidx.compose.ui.draw.scale
import androidx.compose.foundation.BorderStroke
import androidx.compose.ui.Alignment
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.shape.RoundedCornerShape
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var authManager: SupabaseAuthManager

    @Inject
    lateinit var preferencesManager: PreferencesManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Initialize Notification Channel
        NotificationHelper.createNotificationChannel(this)
        
        // Request post notifications permission on Android 13+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
        }
        
        setContent {
            val isDarkTheme by preferencesManager.darkModeFlow.collectAsState(initial = true)
            
            // Sync with ThemeState so that settings switch is in sync
            LaunchedEffect(isDarkTheme) {
                ThemeState.setDarkMode(isDarkTheme)
            }
            
            SocialShieldTheme(darkTheme = isDarkTheme) {
                SocialShieldApp(isLoggedIn = authManager.isUserLoggedIn)
            }
        }
    }
}

object Routes {
    const val SPLASH = "splash"
    const val ONBOARDING = "onboarding"
    const val AUTH = "auth"
    const val HOME = "home"
    const val SCAN = "scan/{scanType}"
    const val PROCESSING = "processing"
    const val RESULT = "result/{scanId}"
    const val HISTORY = "history"
    const val FRAUD_MAP = "fraud_map"
    const val SETTINGS = "settings"

    fun scan(type: ScanType) = "scan/${type.name}"
    fun result(scanId: String) = "result/$scanId"
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SocialShieldApp(isLoggedIn: Boolean) {
    val navController = rememberNavController()
    val currentRoute by navController.currentBackStackEntryAsState()
    val showBottomBar = currentRoute?.destination?.route in listOf(
        Routes.HOME, Routes.HISTORY, Routes.FRAUD_MAP, Routes.SETTINGS
    )

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
        bottomBar = {
            if (showBottomBar) {
                ShieldBottomBar(
                    currentRoute = currentRoute?.destination?.route,
                    onNavigate = { route ->
                        navController.navigate(route) {
                            popUpTo(Routes.HOME) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                )
            }
        }
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Routes.SPLASH,
            modifier = Modifier.padding(padding),
            enterTransition = { slideInHorizontally(tween(300)) { it } + fadeIn(tween(300)) },
            exitTransition = { slideOutHorizontally(tween(300)) { -it } + fadeOut(tween(300)) },
            popEnterTransition = { slideInHorizontally(tween(300)) { -it } + fadeIn(tween(300)) },
            popExitTransition = { slideOutHorizontally(tween(300)) { it } + fadeOut(tween(300)) }
        ) {
            composable(Routes.SPLASH) {
                SplashScreen(
                    onNavigateNext = {
                        val destination = if (isLoggedIn) Routes.HOME else Routes.ONBOARDING
                        navController.navigate(destination) {
                            popUpTo(Routes.SPLASH) { inclusive = true }
                        }
                    }
                )
            }

            composable(Routes.ONBOARDING) {
                OnboardingScreen(
                    onGetStarted = {
                        navController.navigate(Routes.AUTH) {
                            popUpTo(Routes.ONBOARDING) { inclusive = true }
                        }
                    }
                )
            }

            composable(Routes.AUTH) {
                AuthScreen(
                    onAuthSuccess = {
                        navController.navigate(Routes.HOME) {
                            popUpTo(Routes.AUTH) { inclusive = true }
                        }
                    }
                )
            }

            composable(Routes.HOME) {
                HomeScreen(
                    onScanClick = { type -> navController.navigate(Routes.scan(type)) },
                    onHistoryClick = { navController.navigate(Routes.HISTORY) },
                    onFraudMapClick = { navController.navigate(Routes.FRAUD_MAP) },
                    onScanDetailClick = { scanId -> navController.navigate(Routes.result(scanId)) }
                )
            }

            composable(
                Routes.SCAN,
                arguments = listOf(navArgument("scanType") { type = NavType.StringType })
            ) { entry ->
                val scanTypeName = entry.arguments?.getString("scanType") ?: ScanType.IMAGE.name
                val scanType = ScanType.valueOf(scanTypeName)
                ScanScreen(
                    scanType = scanType,
                    onBack = { navController.popBackStack() },
                    onResultReady = { scanId ->
                        navController.navigate(Routes.result(scanId)) {
                            popUpTo(Routes.HOME) { inclusive = false }
                        }
                    }
                )
            }

            composable(
                Routes.RESULT,
                arguments = listOf(navArgument("scanId") { type = NavType.StringType })
            ) { entry ->
                val scanId = entry.arguments?.getString("scanId") ?: ""
                ResultScreen(
                    scanId = scanId,
                    onBack = { navController.popBackStack() },
                    onScanAgain = {
                        navController.navigate(Routes.HOME) {
                            popUpTo(Routes.HOME) { inclusive = false }
                        }
                    }
                )
            }

            composable(Routes.HISTORY) {
                HistoryScreen(
                    onBack = { navController.popBackStack() },
                    onScanDetail = { scanId -> navController.navigate(Routes.result(scanId)) }
                )
            }

            composable(Routes.FRAUD_MAP) {
                FraudMapScreen(onBack = { navController.popBackStack() })
            }

            composable(Routes.SETTINGS) {
                SettingsScreen(
                    onBack = { navController.popBackStack() },
                    onSignOut = {
                        navController.navigate(Routes.AUTH) {
                            popUpTo(0) { inclusive = true }
                        }
                    }
                )
            }
        }
    }
}

@Composable
fun ShieldBottomBar(currentRoute: String?, onNavigate: (String) -> Unit) {
    val items = listOf(
        Triple(Routes.HOME, Icons.Default.Home, "Home"),
        Triple(Routes.HISTORY, Icons.Default.History, "History"),
        Triple(Routes.FRAUD_MAP, Icons.Default.Public, "Map"),
        Triple(Routes.SETTINGS, Icons.Default.Settings, "Settings")
    )

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 8.dp)
    ) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .height(64.dp),
            shape = RoundedCornerShape(32.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f)
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp),
            border = BorderStroke(
                width = 1.dp,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.15f)
            )
        ) {
            Row(
                modifier = Modifier.fillMaxSize(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                items.forEach { (route, icon, label) ->
                    val selected = currentRoute == route
                    val animatedScale by animateFloatAsState(
                        targetValue = if (selected) 1.15f else 1.0f,
                        animationSpec = spring(dampingRatio = 0.6f, stiffness = 300f),
                        label = "scale"
                    )
                    val tintColor = if (selected) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                    }

                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxHeight()
                            .clickable(
                                interactionSource = remember { androidx.compose.foundation.interaction.MutableInteractionSource() },
                                indication = null,
                                onClick = { onNavigate(route) }
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center
                        ) {
                            Box(
                                modifier = Modifier
                                    .scale(animatedScale)
                                    .size(32.dp)
                                    .clip(RoundedCornerShape(10.dp))
                                    .background(
                                        if (selected) {
                                            MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                                        } else {
                                            Color.Transparent
                                        }
                                    ),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    icon,
                                    contentDescription = label,
                                    tint = tintColor,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                            Spacer(Modifier.height(2.dp))
                            Text(
                                label,
                                fontSize = 10.sp,
                                fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                                color = tintColor
                            )
                        }
                    }
                }
            }
        }
    }
}
