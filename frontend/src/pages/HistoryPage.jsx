// ─── History Page ─────────────────────────────────────────────────────────────
import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHistory, deleteScan } from '../api';
import { useAuth } from '../AuthContext';
import { supabase, isSupabaseConfigured } from '../supabase';

const FILTERS = ['ALL', 'IMAGE', 'VIDEO', 'AUDIO', 'TEXT', 'URL', 'PROFILE'];
const ICONS = { IMAGE:'🖼️', VIDEO:'🎬', AUDIO:'🎙️', TEXT:'📝', URL:'🔗', PROFILE:'👤' };

const DEMO_SCANS = Array.from({ length: 8 }, (_, i) => ({
  id: `demo_${i}`,
  scanId: `demo_${i}`,
  mediaType: ['IMAGE','VIDEO','AUDIO','TEXT','URL','PROFILE'][i % 6],
  verdict: ['FAKE','REAL','SUSPICIOUS','REAL','FAKE','REAL','SUSPICIOUS','REAL'][i],
  confidence: parseFloat((70 + Math.random() * 28).toFixed(1)),
  timestamp: new Date(Date.now() - i * 86400000 * 1.5).toISOString(),
}));

function VerdictBadge({ verdict }) {
  const map = { FAKE:['verdict-fake','🔴 FAKE'], SUSPICIOUS:['verdict-suspicious','⚠️ SUSP.'], REAL:['verdict-real','✅ REAL'] };
  const [cls, label] = map[verdict?.toUpperCase()] || map.REAL;
  return <span className={`verdict-badge ${cls}`}>{label}</span>;
}

export default function HistoryPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [filter, setFilter] = useState('ALL');
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (type) => {
    setLoading(true);
    let items = null;

    // 1. Try backend API first
    try {
      const r = await getHistory(type === 'ALL' ? null : type);
      if (r.data?.items && r.data.items.length > 0) {
        items = r.data.items;
      }
    } catch (e) {
      console.warn("Backend getHistory failed, falling back to direct Supabase query:", e);
    }

    // 2. Direct Supabase fallback for instant live sync
    if ((!items || items.length === 0) && isSupabaseConfigured() && (user?.id || user?.uid)) {
      const uid = user.id || user.uid;
      try {
        let q = supabase
          .from('scans')
          .select('*')
          .eq('user_id', uid)
          .order('created_at', { ascending: false });

        if (type && type !== 'ALL') {
          q = q.eq('media_type', type.toUpperCase());
        }

        const { data, error } = await q;
        if (!error && data && data.length > 0) {
          items = data;
        }
      } catch (err) {
        console.error("Direct Supabase history error:", err);
      }
    }

    setScans(items || []);
    setLoading(false);
  }, [user?.id, user?.uid]);

  useEffect(() => {
    load(filter);
  }, [filter, load]);

  // Live Realtime Subscriptions for Multi-Device Android / Web synchronization
  useEffect(() => {
    if (isSupabaseConfigured()) {
      const channel = supabase
        .channel(`realtime-history-sync-channel`)
        .on(
          'postgres_changes',
          { event: '*', schema: 'public', table: 'scans' },
          (payload) => {
            console.log('[Supabase Realtime] Scan change event received in HistoryPage:', payload);
            load(filter);
          }
        )
        .subscribe();

      return () => {
        supabase.removeChannel(channel);
      };
    }
  }, [filter, load]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await deleteScan(id);
      setScans((prev) => prev.filter((s) => (s.id !== id && s.scanId !== id && s.scan_id !== id)));
    } catch (err) {
      console.error("Failed to delete scan:", err);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Scan History</h1>
        <p>Your complete multi-device scan activity log</p>
      </div>

      {/* Filter chips */}
      <div className="section" style={{ paddingBottom: 0 }}>
        <div style={{ display:'flex', gap:8, flexWrap:'wrap', marginBottom:20 }}>
          {FILTERS.map((f) => (
            <button key={f} id={`filter-${f.toLowerCase()}`} className={`chip ${filter===f?'active':''}`} onClick={() => setFilter(f)}>
              {f === 'ALL' ? '🌐 All' : `${ICONS[f]} ${f}`}
            </button>
          ))}
        </div>
      </div>

      <div className="section">
        {loading ? (
          <div style={{ display:'flex', justifyContent:'center', padding:48 }}><div className="spinner" style={{ width:36, height:36 }} /></div>
        ) : scans.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <h3 style={{ color:'rgba(255,255,255,0.5)', fontSize:16, marginBottom:6 }}>No scans found</h3>
            <p style={{ fontSize:13 }}>Start scanning on Web or Android to see synchronized records here</p>
            <button className="btn-neon" style={{ marginTop:20 }} onClick={() => navigate('/home')}>Start Scanning</button>
          </div>
        ) : (
          <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
            {scans.map((scan) => {
              const sid = scan.id || scan.scanId || scan.scan_id;
              const mtype = scan.mediaType || scan.media_type || 'SCAN';
              const ts = scan.timestamp || scan.created_at;
              return (
                <div key={sid} className="history-item" onClick={() => navigate(`/result/${sid}`)}>
                  <div className="history-icon-box" style={{ background:'rgba(0,212,255,0.08)', color:'var(--neon-blue)' }}>
                    {ICONS[mtype] || '🛡️'}
                  </div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ fontWeight:600, fontSize:14 }}>{mtype} Scan</div>
                    <div style={{ fontSize:12, color:'rgba(255,255,255,0.4)', marginTop:2 }}>
                      {ts ? new Date(ts).toLocaleString() : 'Just now'}
                    </div>
                  </div>
                  <div style={{ display:'flex', alignItems:'center', gap:12, flexShrink:0 }}>
                    <VerdictBadge verdict={scan.verdict} />
                    <span style={{ color:'rgba(255,255,255,0.4)', fontSize:13 }}>
                      {scan.confidence ? scan.confidence.toFixed(0) : '0'}%
                    </span>
                    <button
                      onClick={(e) => handleDelete(sid, e)}
                      style={{ background:'none', border:'none', cursor:'pointer', color:'rgba(255,255,255,0.25)', fontSize:18, padding:4 }}
                      title="Delete scan"
                    >
                      🗑️
                    </button>
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
