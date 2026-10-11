package com.socialshield.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.hilt.navigation.compose.hiltViewModel
import com.socialshield.ui.viewmodel.SettingsViewModel
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.socialshield.ui.components.GlassCard
import com.socialshield.ui.components.NeonButton
import com.socialshield.ui.theme.*

// ─── Fraud Map Screen ─────────────────────────────────────────────────────────

data class FraudReport(val city: String, val country: String, val count: Int, val type: String, val severity: String)

private val SAMPLE_REPORTS = listOf(
    FraudReport("Mumbai", "India", 3201, "Phishing SMS", "HIGH"),
    FraudReport("London", "UK", 2140, "Deepfake Video", "HIGH"),
    FraudReport("New York", "USA", 1842, "Voice Cloning", "HIGH"),
    FraudReport("Jakarta", "Indonesia", 1540, "Phishing URL", "HIGH"),
    FraudReport("Beijing", "China", 980, "Fake Profile", "MEDIUM"),
    FraudReport("Dubai", "UAE", 890, "Crypto Scam", "MEDIUM"),
    FraudReport("Lagos", "Nigeria", 620, "Romance Scam", "MEDIUM"),
    FraudReport("São Paulo", "Brazil", 540, "Identity Theft", "LOW"),
    FraudReport("Sydney", "Australia", 210, "Fake Lottery", "LOW")
)

@Composable
fun FraudMapScreen(onBack: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Brush.verticalGradient(listOf(DeepBlack, DarkSurface)))
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            IconButton(onClick = onBack, modifier = Modifier.size(40.dp).clip(CircleShape).background(GlassWhite)) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, null, tint = ContentColor, modifier = Modifier.size(20.dp))
            }
            Column {
                Text("Global Fraud Map", color = ContentColor, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                Text("Live threat intelligence", color = ContentColor.copy(0.5f), fontSize = 12.sp)
            }
        }

        // Heat indicator legend
        GlassCard(modifier = Modifier.padding(horizontal = 16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                listOf("LOW" to RiskLow, "MEDIUM" to RiskMedium, "HIGH" to RiskHigh).forEach { (label, color) ->
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Box(Modifier.size(10.dp).clip(CircleShape).background(color))
                        Text(label, color = color, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("12,655", color = NeonBlue, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    Text("total reports", color = ContentColor.copy(0.5f), fontSize = 10.sp)
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Simulated world map (heatmap cells)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(200.dp)
                .padding(horizontal = 16.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(Color(0xFF0A0A2E))
                .border(1.dp, GlassBorder, RoundedCornerShape(16.dp)),
            contentAlignment = Alignment.Center
        ) {
            androidx.compose.foundation.Canvas(Modifier.fillMaxSize()) {
                // Draw simplified world map dots
                val hotspots = listOf(
                    Offset(0.72f, 0.45f) to RiskHigh,    // India (South Asia - High)
                    Offset(0.52f, 0.6f) to RiskMedium,   // Nigeria (Africa - Medium)
                    Offset(0.48f, 0.32f) to RiskHigh,    // UK (Europe - High)
                    Offset(0.2f, 0.38f) to RiskHigh,     // New York (North America - High)
                    Offset(0.82f, 0.42f) to RiskMedium,  // Beijing (East Asia - Medium)
                    Offset(0.3f, 0.65f) to RiskLow,      // Brazil (South America - Low)
                    Offset(0.78f, 0.56f) to RiskHigh,    // Jakarta (SEA - High)
                    Offset(0.6f, 0.42f) to RiskMedium,   // Dubai (Middle East - Medium)
                    Offset(0.85f, 0.72f) to RiskLow      // Sydney (Oceania - Low)
                )
                hotspots.forEach { (pos, color) ->
                    repeat(3) { ring ->
                        drawCircle(
                            color.copy(alpha = 0.15f / (ring + 1)),
                            radius = (20f + ring * 15f),
                            center = Offset(size.width * pos.x, size.height * pos.y)
                        )
                    }
                    drawCircle(color, radius = 6f, center = Offset(size.width * pos.x, size.height * pos.y))
                }
            }
            Text("Interactive Map · Tap reports for details", color = ContentColor.copy(0.3f), fontSize = 11.sp)
        }

        Spacer(Modifier.height(16.dp))

        Text("Top Fraud Hotspots", color = ContentColor, fontSize = 16.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 16.dp))
        Spacer(Modifier.height(8.dp))

        LazyColumn(
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(SAMPLE_REPORTS) { report ->
                val color = when (report.severity) { "HIGH" -> RiskHigh; "MEDIUM" -> RiskMedium; else -> RiskLow }
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(14.dp))
                        .background(GlassWhite)
                        .border(1.dp, GlassBorder, RoundedCornerShape(14.dp))
                        .padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Box(Modifier.size(40.dp).clip(CircleShape).background(color.copy(0.15f)), contentAlignment = Alignment.Center) {
                        Icon(Icons.Default.Warning, null, tint = color, modifier = Modifier.size(20.dp))
                    }
                    Column(modifier = Modifier.weight(1f)) {
                        Text("${report.city}, ${report.country}", color = ContentColor, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                        Text(report.type, color = ContentColor.copy(0.5f), fontSize = 12.sp)
                    }
                    Column(horizontalAlignment = Alignment.End) {
                        Text("${report.count}", color = color, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                        Text("reports", color = ContentColor.copy(0.4f), fontSize = 10.sp)
                    }
                }
            }
        }
    }
}

// ─── Settings Screen ──────────────────────────────────────────────────────────

@Composable
fun SettingsScreen(
    onBack: () -> Unit,
    onSignOut: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val darkMode by viewModel.darkMode.collectAsState()
    val notifications by viewModel.threatAlerts.collectAsState()
    val localProcessing by viewModel.localProcessing.collectAsState()
    val autoSave by viewModel.autoSaveScans.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Brush.verticalGradient(listOf(DeepBlack, DarkSurface)))
            .verticalScroll(rememberScrollState())
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            IconButton(onClick = onBack, modifier = Modifier.size(40.dp).clip(CircleShape).background(GlassWhite)) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, null, tint = ContentColor, modifier = Modifier.size(20.dp))
            }
            Text("Settings", color = ContentColor, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        }

        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            SettingsSection("Appearance") {
                SettingsToggle("Dark Mode", "Use dark cybersecurity theme", Icons.Default.DarkMode, NeonBlue, darkMode) { viewModel.setDarkMode(it) }
            }

            SettingsSection("Privacy & Security") {
                SettingsToggle("Local Processing", "Process media on-device when possible", Icons.Default.PhonelinkLock, NeonPurple, localProcessing) { viewModel.setLocalProcessing(it) }
                SettingsToggle("Auto-Save Scans", "Save scan results to history", Icons.Default.Save, NeonCyan, autoSave) { viewModel.setAutoSaveScans(it) }
            }

            SettingsSection("Notifications") {
                SettingsToggle("Threat Alerts", "Notify on new fraud threats in your area", Icons.Default.NotificationsActive, NeonPink, notifications) { viewModel.setThreatAlerts(it) }
            }

            SettingsSection("Account") {
                GlassCard {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        val user by viewModel.currentUser.collectAsState()
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            Box(Modifier.size(44.dp).clip(CircleShape).background(NeonBlue.copy(0.2f)), contentAlignment = Alignment.Center) {
                                Icon(Icons.Default.Person, null, tint = NeonBlue, modifier = Modifier.size(24.dp))
                            }
                            Column {
                                Text(user?.displayName ?: user?.email?.substringBefore('@') ?: "Shield User", color = ContentColor, fontSize = 15.sp, fontWeight = FontWeight.SemiBold)
                                Text(user?.email ?: "", color = ContentColor.copy(0.5f), fontSize = 12.sp)
                            }
                        }
                        HorizontalDivider(color = GlassBorder)
                        TextButton(
                            onClick = {
                                viewModel.signOut()
                                onSignOut()
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.AutoMirrored.Filled.Logout, null, tint = RiskHigh, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text("Sign Out", color = RiskHigh, fontWeight = FontWeight.Medium)
                        }
                    }
                }
            }

            // App info
            GlassCard {
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                    Text("SocialShield", color = ContentColor, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    Text("Version 1.0.0", color = ContentColor.copy(0.5f), fontSize = 13.sp)
                    Spacer(Modifier.height(4.dp))
                    Text("AI-Powered Digital Fraud Protection", color = NeonBlue.copy(0.7f), fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
fun SettingsSection(title: String, content: @Composable () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(title, color = NeonBlue, fontSize = 12.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
        content()
    }
}

@Composable
fun SettingsToggle(
    title: String,
    subtitle: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    GlassCard {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Box(Modifier.size(40.dp).clip(CircleShape).background(color.copy(0.15f)), contentAlignment = Alignment.Center) {
                Icon(icon, null, tint = color, modifier = Modifier.size(20.dp))
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(title, color = ContentColor, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                Text(subtitle, color = ContentColor.copy(0.5f), fontSize = 11.sp, lineHeight = 14.sp)
            }
            Switch(
                checked = checked,
                onCheckedChange = onCheckedChange,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = ContentColor,
                    checkedTrackColor = color,
                    uncheckedThumbColor = ContentColor.copy(0.5f),
                    uncheckedTrackColor = GlassWhite
                )
            )
        }
    }
}
