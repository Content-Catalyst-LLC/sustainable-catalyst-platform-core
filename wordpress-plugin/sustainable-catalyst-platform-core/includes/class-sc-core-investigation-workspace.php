<?php
if (!defined('ABSPATH')) { exit; }
final class SC_Core_Investigation_Workspace_320 {
  public static function init(){ add_shortcode('sc_core_investigation_workspace',[__CLASS__,'render']); }
  public static function render($atts=[]){
    $base=apply_filters('sc_platform_core_backend_url', defined('SC_PLATFORM_CORE_BACKEND_URL') ? SC_PLATFORM_CORE_BACKEND_URL : '');
    $id='sc-core-investigation-workspace-'.wp_rand(1000,999999);
    ob_start(); ?>
    <section id="<?php echo esc_attr($id); ?>" class="sc-core-investigation-workspace" data-backend="<?php echo esc_attr(rtrim($base,'/')); ?>">
      <div class="sc-iw-head"><strong>Unified Investigation Workspace</strong><span>Platform Core v3.20.0</span></div>
      <div class="sc-iw-status">Connecting to investigation capabilities…</div>
      <div class="sc-iw-grid" hidden><div><b>Evidence & references</b><p>Link governed research and forensic objects without flattening provenance.</p></div><div><b>Relationships & views</b><p>Build explicit connection graphs and analytical views over the same case.</p></div><div><b>Snapshots & handoffs</b><p>Freeze reproducible investigation states and move them across Catalyst products.</p></div></div>
    </section>
    <script>(function(){const e=document.getElementById(<?php echo wp_json_encode($id); ?>);if(!e)return;const b=e.dataset.backend,s=e.querySelector('.sc-iw-status'),g=e.querySelector('.sc-iw-grid');if(!b){s.textContent='Backend URL is not configured.';return;}fetch(b+'/api/v1/investigation-workspace/capabilities',{credentials:'omit'}).then(r=>{if(!r.ok)throw new Error(r.status);return r.json()}).then(d=>{s.textContent=(d.capability||'Unified Investigation Workspace')+' · Core '+(d.version||'3.20.0')+' online';g.hidden=false}).catch(()=>{s.textContent='Investigation workspace backend unavailable.'})})();</script>
    <style>.sc-core-investigation-workspace{border:1px solid #222;padding:18px;background:#0a0a0a;color:#f4f4f4}.sc-iw-head{display:flex;justify-content:space-between;gap:18px;border-bottom:1px solid #333;padding-bottom:10px}.sc-iw-status{margin:14px 0;color:#9ee6b1}.sc-iw-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.sc-iw-grid>div{border:1px solid #292929;padding:12px}.sc-iw-grid p{margin:.5em 0 0;color:#c7c7c7}</style>
    <?php return ob_get_clean();
  }
}
SC_Core_Investigation_Workspace_320::init();
