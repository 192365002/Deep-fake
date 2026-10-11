// ─── Home Page ────────────────────────────────────────────────────────────────
import { useEffect, useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { getUserStats, getHistory } from '../api';
import { supabase, isSupabaseConfigured } from '../supabase';

const SCAN_TYPES = [
  { type: 'image',   icon: '🖼️',  label: 'Scan Image',   sub: 'Detect AI-generated faces',        color: '#00D4FF', bg: 'rgba(0,212,255,0.12)'   },
  { type: 'video',   icon: '🎬',  label: 'Scan Video',   sub: 'Frame-by-frame deepfake analysis', color: '#8B5CF6', bg: 'rgba(139,92,246,0.12)'  },
  { type: 'audio',   icon: '🎙️', label: 'Scan Audio',   sub: 'Voice clone detection',            color: '#06FFA5', bg: 'rgba(6,255,165,0.12)'   },
  { type: 'text',    icon: '📝',  label: 'Scan Text',    sub: 'Scam & phishing message check',   color: '#FF3CAC', bg: 'rgba(255,60,172,0.12)'  },
  { type: 'url',     icon: '🔗',  label: 'Scan URL',     sub: 'Safe Browsing & VirusTotal',       color: '#FFB800', bg: 'rgba(255,184,0,0.12)'   },
  { type: 'profile', icon: '👤',  label: 'Scan Profile', sub: 'Fake account detection',           color: '#00E5FF', bg: 'rgba(0,229,255,0.12)'   },
];

function VerdictBadge({ verdict }) {
  const map = { FAKE: ['verdict-fake','🔴 FAKE'], SUSPICIOUS: ['verdict-suspicious','⚠️ SUSPICIOUS'], REAL: ['verdict-real','✅ REAL'] };
  const [cls, label] = map[verdict?.toUpperCase()] || map.REAL;
  return <span className={`verdict-badge ${cls}`}>{label}</span>;
}

export default function HomePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ totalScans: 0, fakeDetected: 0, suspiciousDetected: 0, safeDetected: 0, trustScore: 100 });
  const [recent, setRecent] = useState([]);
  const [statsLoading, setStatsLoading] = useState(true);

  const loadData = useCallback(async () => {
    setStatsLoading(true);
    let loadedStats = null;
    let loadedRecent = [];

    // 1. Try backend API
    try {
      const statsRes = await getUserStats();
      if (statsRes.data && (statsRes.data.total_scans > 0 || statsRes.data.totalScans > 0)) {
        loadedStats = {
          totalScans: statsRes.data.total_scans ?? statsRes.data.totalScans ?? 0,
          fakeDetected: statsRes.data.fake_detected ?? statsRes.data.fakeDetected ?? 0,
          suspiciousDetected: statsRes.data.suspicious_detected ?? statsRes.data.suspiciousDetected ?? 0,
          safeDetected: statsRes.data.safe_detected ?? statsRes.data.safeDetected ?? 0,
          trustScore: statsRes.data.trust_score ?? statsRes.data.trustScore ?? 100,
        };
      }
    } catch {}

    try {
      const histRes = await getHistory();
      if (histRes.data?.items?.length > 0) {
        loadedRecent = histRes.data.items.slice(0, 4);
      }
    } catch {}

    // 2. Direct Supabase fallback for instant real-time synchronization
    let uid = user?.id || user?.uid;
    if (!uid && isSupabaseConfigured()) {
      try {
        const { data: { user: sbUser } } = await supabase.auth.getUser();
        if (sbUser) uid = sbUser.id;
      } catch {}
    }

    if (isSupabaseConfigured() && uid) {
      try {
        const { data: dbScans } = await supabase
          .from('scans')
          .select('*')
          .eq('user_id', uid)
          .order('created_at', { ascending: false });

        if (dbScans && dbScans.length > 0) {
          if (!loadedRecent || loadedRecent.length === 0 || dbScans.length > loadedRecent.length) {
            loadedRecent = dbScans.slice(0, 4);
          }
          const total = dbScans.length;
          const fake = dbScans.filter(s => String(s.verdict).toUpperCase() === 'FAKE' || String(s.verdict).toUpperCase() === 'DANGEROUS').length;
          const suspicious = dbScans.filter(s => String(s.verdict).toUpperCase() === 'SUSPICIOUS').length;
          const safe = dbScans.filter(s => ['SAFE', 'REAL'].includes(String(s.verdict).toUpperCase())).length;
          const trust = total > 0 ? Math.round(((safe + 0.5 * suspicious) / total) * 100) : 100;
          if (!loadedStats || total >= (loadedStats.totalScans || 0)) {
            loadedStats = { totalScans: total, fakeDetected: fake, suspiciousDetected: suspicious, safeDetected: safe, trustScore: trust };
          }
        }
      } catch (err) {
        console.error("Direct Supabase query error:", err);
      }
    }

    setStats(loadedStats || { totalScans: 0, fakeDetected: 0, suspiciousDetected: 0, safeDetected: 0, trustScore: 100 });
    setRecent(loadedRecent || []);
    setStatsLoading(false);
  }, [user?.id, user?.uid]);

  // Initial load + Supabase Realtime synchronization
  useEffect(() => {
    loadData();

    // Bidirectional Synchronization: Live WebSocket listener
    if (isSupabaseConfigured()) {
      const channel = supabase
        .channel(`realtime-scans-home-live`)
        .on(
          'postgres_changes',
          { event: '*', schema: 'public', table: 'scans' },
          (payload) => {
            console.log('[Supabase Realtime] Scan event received on Web:', payload);
            loadData();
          }
        )
        .on(
          'postgres_changes',
          { event: '*', schema: 'public', table: 'user_stats' },
          (payload) => {
            console.log('[Supabase Realtime] User stats updated on Web:', payload);
            loadData();
          }
        )
        .subscribe();

      return () => {
        supabase.removeChannel(channel);
      };
    }
  }, [loadData]);

  const scoreColor = stats.trustScore >= 80 ? '#06FFA5' : stats.trustScore >= 50 ? '#FFB800' : '#FF3B3B';
  const greetName = user?.displayName || user?.email?.split('@')[0] || 'Shield User';

  return (
    <div style={{ paddingBottom: 40 }}>
      {/* ── Page Header ── */}
      <div className="page-header" style={{ background: 'linear-gradient(180deg, rgba(0,212,255,0.06) 0%, transparent 100%)', padding: '28px 28px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 13, marginBottom: 4 }}>Welcome back</p>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800 }}>{greetName}</h1>
          </div>

          {/* Trust Score */}
          <div className="trust-score-card" style={{ minWidth: 220 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>AI Trust Score</p>
                <div className="trust-score-value" style={{ color: scoreColor }}>
                  {statsLoading ? '—' : stats.trustScore}
                  <span style={{ fontSize: 18, color: 'rgba(255,255,255,0.4)', fontWeight: 400 }}>/100</span>
                </div>
                <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginTop: 4 }}>
                  {stats.trustScore >= 80 ? 'Excellent protection' : stats.trustScore >= 50 ? 'Moderate risk' : 'High threat exposure'}
                </p>
              </div>
              <div style={{ fontSize: 40, opacity: 0.3 }}>🛡️</div>
            </div>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid-4" style={{ marginTop: 20 }}>
          {[
            { label: 'Total Scans', value: stats.totalScans, color: '#00D4FF' },
            { label: 'Safe Profiles', value: stats.safeDetected, color: '#06FFA5' },
            { label: 'Suspicious', value: stats.suspiciousDetected, color: '#FFB800' },
            { label: 'Fake Detected', value: stats.fakeDetected, color: '#FF3B3B' },
          ].map(({ label, value, color }) => (
            <div key={label} className="stat-card">
              <div className="stat-value" style={{ color }}>{statsLoading ? '—' : value}</div>
              <div className="stat-label">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Scan Types ── */}
      <div className="section">
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Scan &amp; Detect</h2>
        <div className="scan-grid" style={{ padding: 0 }}>
          {SCAN_TYPES.map(({ type, icon, label, sub, color, bg }) => (
            <div
              key={type}
              id={`scan-btn-${type}`}
              className="scan-type-card"
              onClick={() => navigate(`/scan/${type}`)}
              style={{ cursor: 'pointer' }}
            >
              <div className="scan-icon" style={{ background: bg }}>
                {icon}
              </div>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>{label}</h3>
              <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', lineHeight: 1.4 }}>{sub}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Recent Scans ── */}
      <div className="section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>Recent Scans</h2>
          <Link to="/history" style={{ color: 'var(--neon-blue)', fontSize: 13, textDecoration: 'none' }}>
            View all →
          </Link>
        </div>

        {recent.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🛡️</div>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 14 }}>No scans yet. Choose a detection type above to get started.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {recent.map((scan) => {
              const sid = scan.id || scan.scanId;
              const mtype = scan.mediaType || scan.media_type;
              return (
                <div
                  key={sid}
                  className="history-item"
                  onClick={() => navigate(`/result/${sid}`)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                    <div className="history-icon-box" style={{ background: 'rgba(0,212,255,0.08)', color: 'var(--neon-blue)' }}>
                      🛡️
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{mtype} Scan</div>
                      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>
                        {new Date(scan.timestamp || scan.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
                    <VerdictBadge verdict={scan.verdict} />
                    <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                      {scan.confidence?.toFixed(0)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
