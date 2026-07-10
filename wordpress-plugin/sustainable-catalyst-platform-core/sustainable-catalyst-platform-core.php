<?php
/**
 * Plugin Name: Sustainable Catalyst Platform Core
 * Description: WordPress status and registry lookup client for Sustainable Catalyst Platform Core v2.0.0.
 * Version: 2.2.0
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SCPC_VERSION', '2.2.0');
define('SCPC_OPTION_BACKEND_URL', 'scpc_backend_url');
define('SCPC_OPTION_READ_KEY', 'scpc_read_key');

function scpc_register_settings() {
    register_setting('scpc_settings', SCPC_OPTION_BACKEND_URL, [
        'type' => 'string',
        'sanitize_callback' => 'esc_url_raw',
        'default' => '',
    ]);
    register_setting('scpc_settings', SCPC_OPTION_READ_KEY, [
        'type' => 'string',
        'sanitize_callback' => 'sanitize_text_field',
        'default' => '',
    ]);
}
add_action('admin_init', 'scpc_register_settings');

function scpc_admin_menu() {
    add_options_page(
        'Platform Core',
        'Platform Core',
        'manage_options',
        'sc-platform-core',
        'scpc_render_settings_page'
    );
}
add_action('admin_menu', 'scpc_admin_menu');

function scpc_render_settings_page() {
    if (!current_user_can('manage_options')) {
        return;
    }
    $backend = get_option(SCPC_OPTION_BACKEND_URL, '');
    ?>
    <div class="wrap">
        <h1>Sustainable Catalyst Platform Core</h1>
        <p>Configure the shared entity registry backend used by Sustainable Catalyst products.</p>
        <form method="post" action="options.php">
            <?php settings_fields('scpc_settings'); ?>
            <table class="form-table">
                <tr>
                    <th scope="row"><label for="scpc_backend_url">Backend URL</label></th>
                    <td>
                        <input
                            name="<?php echo esc_attr(SCPC_OPTION_BACKEND_URL); ?>"
                            id="scpc_backend_url"
                            type="url"
                            class="regular-text"
                            value="<?php echo esc_attr($backend); ?>"
                            placeholder="https://your-platform-core.onrender.com"
                        />
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="scpc_read_key">Optional read key</label></th>
                    <td>
                        <input
                            name="<?php echo esc_attr(SCPC_OPTION_READ_KEY); ?>"
                            id="scpc_read_key"
                            type="password"
                            class="regular-text"
                            value="<?php echo esc_attr(get_option(SCPC_OPTION_READ_KEY, '')); ?>"
                        />
                        <p class="description">Leave blank while public reads are enabled. Never place the write key in public frontend code.</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
        <h2>Shortcodes</h2>
        <code>[sc_platform_core_status]</code><br />
        <code>[sc_platform_core_entity id="sc:product:workbench"]</code><br />
        <code>[sc_platform_core_relationships id="sc:product:research-librarian"]</code><br />
        <code>[sc_knowledge_explorer]</code><br />
        <code>[sc_evidence_ledger_status]</code><br />
        <code>[sc_evidence_manifest claim_id="sc:claim:..."]</code><br />
        <code>[sc_evidence_explorer]</code>
    </div>
    <?php
}

function scpc_api_get($path) {
    $base = untrailingslashit(get_option(SCPC_OPTION_BACKEND_URL, ''));
    if (!$base) {
        return new WP_Error('scpc_not_configured', 'Platform Core backend URL is not configured.');
    }

    $headers = ['Accept' => 'application/json'];
    $read_key = get_option(SCPC_OPTION_READ_KEY, '');
    if ($read_key) {
        $headers['X-SC-API-Key'] = $read_key;
    }

    $response = wp_remote_get($base . $path, [
        'timeout' => 12,
        'headers' => $headers,
    ]);

    if (is_wp_error($response)) {
        return $response;
    }

    $status = wp_remote_retrieve_response_code($response);
    $body = json_decode(wp_remote_retrieve_body($response), true);

    if ($status < 200 || $status >= 300) {
        return new WP_Error(
            'scpc_api_error',
            isset($body['detail']) ? $body['detail'] : 'Platform Core request failed.'
        );
    }

    return $body;
}

function scpc_status_shortcode() {
    $health = scpc_api_get('/health');
    if (is_wp_error($health)) {
        return '<div class="scpc-card scpc-error"><strong>Platform Core unavailable</strong><p>' .
            esc_html($health->get_error_message()) .
            '</p></div>';
    }

    $stats = scpc_api_get('/v1/stats');
    $entities = (!is_wp_error($stats) && isset($stats['entities'])) ? intval($stats['entities']) : 0;
    $relationships = (!is_wp_error($stats) && isset($stats['relationships'])) ? intval($stats['relationships']) : 0;

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Shared knowledge infrastructure</p>
        <h3>Sustainable Catalyst Platform Core</h3>
        <p>
            <strong>Status:</strong> Online ·
            <strong>Version:</strong> <?php echo esc_html($health['version']); ?> ·
            <strong>Entities:</strong> <?php echo esc_html(number_format_i18n($entities)); ?> ·
            <strong>Relationships:</strong> <?php echo esc_html(number_format_i18n($relationships)); ?>
        </p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_status', 'scpc_status_shortcode');

function scpc_entity_shortcode($atts) {
    $atts = shortcode_atts(['id' => ''], $atts, 'sc_platform_core_entity');
    $entity_id = sanitize_text_field($atts['id']);

    if (!$entity_id) {
        return '<div class="scpc-card scpc-error">Entity ID is required.</div>';
    }

    $entity = scpc_api_get('/v1/entities/' . rawurlencode($entity_id));
    if (is_wp_error($entity)) {
        return '<div class="scpc-card scpc-error"><strong>Entity unavailable</strong><p>' .
            esc_html($entity->get_error_message()) .
            '</p></div>';
    }

    $url = isset($entity['canonical_url']) ? esc_url($entity['canonical_url']) : '';
    ob_start();
    ?>
    <article class="scpc-card">
        <p class="scpc-kicker"><?php echo esc_html($entity['entity_type']); ?></p>
        <h3><?php echo esc_html($entity['name']); ?></h3>
        <?php if (!empty($entity['description'])) : ?>
            <p><?php echo esc_html($entity['description']); ?></p>
        <?php endif; ?>
        <p class="scpc-meta">
            <code><?php echo esc_html($entity['id']); ?></code>
            · <?php echo esc_html($entity['status']); ?>
        </p>
        <?php if ($url) : ?>
            <a class="scpc-button" href="<?php echo $url; ?>">Open resource</a>
        <?php endif; ?>
    </article>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_entity', 'scpc_entity_shortcode');

function scpc_enqueue_styles() {
    wp_register_style(
        'scpc-styles',
        plugins_url('assets/platform-core.css', __FILE__),
        [],
        SCPC_VERSION
    );
    wp_enqueue_style('scpc-styles');
}
add_action('wp_enqueue_scripts', 'scpc_enqueue_styles');


function scpc_relationships_shortcode($atts) {
    $atts = shortcode_atts(['id' => '', 'limit' => 20], $atts, 'sc_platform_core_relationships');
    $entity_id = sanitize_text_field($atts['id']);
    $limit = min(50, max(1, intval($atts['limit'])));
    if (!$entity_id) {
        return '<div class="scpc-card scpc-error">Entity ID is required.</div>';
    }

    $graph = scpc_api_get('/v1/graph/' . rawurlencode($entity_id) . '/neighborhood?statuses=verified&statuses=approved');
    if (is_wp_error($graph)) {
        return '<div class="scpc-card scpc-error"><strong>Relationships unavailable</strong><p>' .
            esc_html($graph->get_error_message()) . '</p></div>';
    }

    ob_start(); ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Knowledge graph</p>
        <h3><?php echo esc_html($graph['root']['name']); ?></h3>
        <?php
        $shown = 0;
        foreach ($graph['groups'] as $group) :
            if ($shown >= $limit) break; ?>
            <div class="scpc-relationship-group">
                <strong><?php echo esc_html(ucfirst($group['direction']) . ' · ' . $group['predicate_label']); ?></strong>
                <ul>
                    <?php foreach ($group['entities'] as $entity) :
                        if ($shown >= $limit) break;
                        $shown++; ?>
                        <li>
                            <?php if (!empty($entity['canonical_url'])) : ?>
                                <a href="<?php echo esc_url($entity['canonical_url']); ?>"><?php echo esc_html($entity['name']); ?></a>
                            <?php else : echo esc_html($entity['name']); endif; ?>
                            <code><?php echo esc_html($entity['id']); ?></code>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>
        <?php endforeach; ?>
        <?php if ($shown === 0) : ?><p>No reviewed relationships are available yet.</p><?php endif; ?>
    </section>
    <?php return ob_get_clean();
}
add_shortcode('sc_platform_core_relationships', 'scpc_relationships_shortcode');

function scpc_knowledge_explorer_shortcode() {
    $base = untrailingslashit(get_option(SCPC_OPTION_BACKEND_URL, ''));
    if (!$base) {
        return '<div class="scpc-card scpc-error">Platform Core backend URL is not configured.</div>';
    }
    return '<section class="scpc-card">' .
        '<p class="scpc-kicker">Knowledge infrastructure</p>' .
        '<h3>Sustainable Catalyst Knowledge Explorer</h3>' .
        '<p>Search registered concepts, tools, sources, datasets, products, and their reviewed relationships.</p>' .
        '<a class="scpc-button" href="' . esc_url($base . '/explorer') . '" target="_blank" rel="noopener">Open Knowledge Explorer</a>' .
        '</section>';
}
add_shortcode('sc_knowledge_explorer', 'scpc_knowledge_explorer_shortcode');


function scpc_evidence_ledger_status_shortcode() {
    $stats = scpc_api_get('/v1/evidence/stats');
    $verification = scpc_api_get('/v1/ledger/verify');

    if (is_wp_error($stats) || is_wp_error($verification)) {
        $error = is_wp_error($stats) ? $stats : $verification;
        return '<div class="scpc-card scpc-error"><strong>Evidence Ledger unavailable</strong><p>' .
            esc_html($error->get_error_message()) .
            '</p></div>';
    }

    $valid = !empty($verification['valid']);
    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Evidence and provenance infrastructure</p>
        <h3>Sustainable Catalyst Evidence Ledger</h3>
        <p>
            <strong>Integrity:</strong>
            <span class="<?php echo $valid ? 'scpc-ledger-valid' : 'scpc-ledger-invalid'; ?>">
                <?php echo $valid ? 'Verified' : 'Verification failed'; ?>
            </span>
            · <strong>Claims:</strong> <?php echo esc_html(number_format_i18n(intval($stats['claims']))); ?>
            · <strong>Evidence records:</strong> <?php echo esc_html(number_format_i18n(intval($stats['evidence_records']))); ?>
            · <strong>Snapshots:</strong> <?php echo esc_html(number_format_i18n(intval($stats['source_snapshots']))); ?>
            · <strong>Ledger entries:</strong> <?php echo esc_html(number_format_i18n(intval($stats['ledger_entries']))); ?>
        </p>
        <?php if (!empty($stats['ledger_head_hash'])) : ?>
            <p class="scpc-meta">Ledger head: <code><?php echo esc_html($stats['ledger_head_hash']); ?></code></p>
        <?php endif; ?>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_evidence_ledger_status', 'scpc_evidence_ledger_status_shortcode');

function scpc_evidence_manifest_shortcode($atts) {
    $atts = shortcode_atts(['claim_id' => ''], $atts, 'sc_evidence_manifest');
    $claim_id = sanitize_text_field($atts['claim_id']);

    if (!$claim_id) {
        return '<div class="scpc-card scpc-error">Claim ID is required.</div>';
    }

    $manifest = scpc_api_get('/v1/evidence/manifests/' . rawurlencode($claim_id));
    if (is_wp_error($manifest)) {
        return '<div class="scpc-card scpc-error"><strong>Evidence manifest unavailable</strong><p>' .
            esc_html($manifest->get_error_message()) .
            '</p></div>';
    }

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Evidence manifest</p>
        <h3><?php echo esc_html($manifest['claim']['claim_text']); ?></h3>
        <p>
            <strong>Evidence:</strong> <?php echo esc_html(count($manifest['evidence'])); ?>
            · <strong>Snapshots:</strong> <?php echo esc_html(count($manifest['snapshots'])); ?>
            · <strong>Calculation traces:</strong> <?php echo esc_html(count($manifest['calculation_traces'])); ?>
            · <strong>Reviews:</strong> <?php echo esc_html(count($manifest['reviews'])); ?>
        </p>
        <p class="scpc-meta">Manifest hash: <code><?php echo esc_html($manifest['manifest_hash']); ?></code></p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_evidence_manifest', 'scpc_evidence_manifest_shortcode');

function scpc_evidence_explorer_shortcode() {
    $base = untrailingslashit(get_option(SCPC_OPTION_BACKEND_URL, ''));
    if (!$base) {
        return '<div class="scpc-card scpc-error">Platform Core backend URL is not configured.</div>';
    }

    return '<section class="scpc-card">' .
        '<p class="scpc-kicker">Evidence and provenance</p>' .
        '<h3>Sustainable Catalyst Evidence Explorer</h3>' .
        '<p>Inspect claims, source snapshots, evidence records, calculation traces, review history, manifests, and ledger integrity.</p>' .
        '<a class="scpc-button" href="' . esc_url($base . '/evidence-explorer') . '" target="_blank" rel="noopener">Open Evidence Explorer</a>' .
        '</section>';
}
add_shortcode('sc_evidence_explorer', 'scpc_evidence_explorer_shortcode');
