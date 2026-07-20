<?php
/**
 * Plugin Name: Sustainable Catalyst Platform Core
 * Description: WordPress connector for Sustainable Catalyst Platform Core registry, graph, evidence, developer, gateway, free live-data, international-law, scientific-data, and official-statistics services.
 * Version: 2.7.3
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SCPC_VERSION', '2.7.3');
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
        <code>[sc_platform_core_live_data_status]</code><br />
        <code>[sc_platform_core_international_law_status]</code><br />
        <code>[sc_platform_core_science_status]</code><br />
        <code>[sc_platform_core_economics_status]</code><br />
        <code>[sc_platform_core_entity id="sc:product:workbench"]</code><br />
        <code>[sc_platform_core_relationships id="sc:product:research-librarian"]</code><br />
        <code>[sc_knowledge_explorer]</code><br />
        <code>[sc_evidence_ledger_status]</code><br />
        <code>[sc_evidence_manifest claim_id="sc:claim:..."]</code><br />
        <code>[sc_evidence_explorer]</code><br />
        <code>[sc_developer_portal]</code><br />
        <code>[sc_public_api_plans]</code><br />
        <code>[sc_trust_center]</code><br />
        <code>[sc_trust_status]</code><br />
        <code>[sc_dossier_center]</code><br />
        <code>[sc_signature_dossier id="sc:dossier:..."]</code><br />
        <code>[sc_workflow_status id="sc:workflow-run:..."]</code>
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


function scpc_live_data_status_shortcode() {
    $health = scpc_api_get('/v1/live/connectors/health');
    $stats = scpc_api_get('/v1/live/stats');

    if (is_wp_error($health) || is_wp_error($stats)) {
        $error = is_wp_error($health) ? $health : $stats;
        return '<div class="scpc-card scpc-error"><strong>Live Data Gateway unavailable</strong><p>' .
            esc_html($error->get_error_message()) .
            '</p></div>';
    }

    $overall = isset($health['overall_status']) ? sanitize_text_field($health['overall_status']) : 'unknown';
    $strict = !empty($health['strict_free_sources']);
    $operational = isset($health['operational_connectors']) ? intval($health['operational_connectors']) : 0;
    $connector_count = isset($health['connector_count']) ? intval($health['connector_count']) : 0;
    $source_count = isset($stats['sources']) ? intval($stats['sources']) : 0;
    $observation_count = isset($stats['observations']) ? intval($stats['observations']) : 0;

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Free live-data infrastructure</p>
        <h3>Sustainable Catalyst Live Data Gateway</h3>
        <p>
            <strong>Status:</strong> <?php echo esc_html(ucwords(str_replace('_', ' ', $overall))); ?> ·
            <strong>Free-source gate:</strong> <?php echo $strict ? 'Required' : 'Disabled'; ?> ·
            <strong>Sources:</strong> <?php echo esc_html(number_format_i18n($source_count)); ?> ·
            <strong>Connectors:</strong> <?php echo esc_html(number_format_i18n($operational)); ?>/<?php echo esc_html(number_format_i18n($connector_count)); ?> configured ·
            <strong>Observations:</strong> <?php echo esc_html(number_format_i18n($observation_count)); ?>
        </p>
        <p class="scpc-meta">Weather, Earth observation, hazards, economics, and sustainability records retain source, freshness, license, attribution, and provenance metadata.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_live_data_status', 'scpc_live_data_status_shortcode');


function scpc_international_law_status_shortcode() {
    $stats = scpc_api_get('/v1/international-law/stats');
    $health = scpc_api_get('/v1/live/connectors/health');

    if (is_wp_error($stats) || is_wp_error($health)) {
        $error = is_wp_error($stats) ? $stats : $health;
        return '<div class="scpc-card scpc-error"><strong>International Law and UN data unavailable</strong><p>' .
            esc_html($error->get_error_message()) .
            '</p></div>';
    }

    $records = isset($stats['records']) ? intval($stats['records']) : 0;
    $public_records = isset($stats['public_records']) ? intval($stats['public_records']) : 0;
    $un_connectors = 0;
    $configured = 0;
    foreach (($health['connectors'] ?? []) as $connector) {
        $id = isset($connector['id']) ? (string) $connector['id'] : '';
        if (strpos($id, 'un.') === 0 || strpos($id, 'unhcr.') === 0 || strpos($id, 'ocha.') === 0 || strpos($id, 'ohchr.') === 0) {
            $un_connectors++;
            if (($connector['configuration_status'] ?? '') === 'configured') {
                $configured++;
            }
        }
    }

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Official-source legal and UN infrastructure</p>
        <h3>International Law and United Nations Connector Pack</h3>
        <p>
            <strong>Version:</strong> <?php echo esc_html(SCPC_VERSION); ?> ·
            <strong>Connectors:</strong> <?php echo esc_html(number_format_i18n($configured)); ?>/<?php echo esc_html(number_format_i18n($un_connectors)); ?> configured ·
            <strong>Legal records:</strong> <?php echo esc_html(number_format_i18n($records)); ?> ·
            <strong>Public records:</strong> <?php echo esc_html(number_format_i18n($public_records)); ?>
        </p>
        <p class="scpc-meta">Records preserve official source, authority class, publication date, citation, content hash, and raw-ingestion provenance. Security Council binding effect is never inferred from a document symbol alone.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_international_law_status', 'scpc_international_law_status_shortcode');

function scpc_science_status_shortcode() {
    $stats = scpc_api_get('/v1/science/stats');
    $health = scpc_api_get('/v1/live/connectors/health');

    if (is_wp_error($stats) || is_wp_error($health)) {
        $error = is_wp_error($stats) ? $stats : $health;
        return '<div class="scpc-card scpc-error"><strong>Scientific Data Connector Pack unavailable</strong><p>' .
            esc_html($error->get_error_message()) .
            '</p></div>';
    }

    $records = isset($stats['records']) ? intval($stats['records']) : 0;
    $public_records = isset($stats['public_records']) ? intval($stats['public_records']) : 0;
    $science_connectors = 0;
    $configured = 0;
    $science_domains = ['earth_science', 'space_science', 'atmospheric_science', 'hydrology', 'biomedical_science', 'chemistry', 'biodiversity', 'materials_science', 'astronomy'];
    foreach (($health['connectors'] ?? []) as $connector) {
        $domain = isset($connector['domain']) ? (string) $connector['domain'] : '';
        if (in_array($domain, $science_domains, true)) {
            $science_connectors++;
            if (($connector['configuration_status'] ?? '') === 'configured') {
                $configured++;
            }
        }
    }

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Free official scientific data infrastructure</p>
        <h3>Sustainable Catalyst Scientific Data Connector Pack</h3>
        <p>
            <strong>Version:</strong> <?php echo esc_html(SCPC_VERSION); ?> ·
            <strong>Connectors:</strong> <?php echo esc_html(number_format_i18n($configured)); ?>/<?php echo esc_html(number_format_i18n($science_connectors)); ?> configured ·
            <strong>Scientific records:</strong> <?php echo esc_html(number_format_i18n($records)); ?> ·
            <strong>Public records:</strong> <?php echo esc_html(number_format_i18n($public_records)); ?>
        </p>
        <p class="scpc-meta">Earth science, hydrology, biomedical, chemical, biodiversity, materials, and astronomy records retain identifiers, access links, license, attribution, content hashes, and raw-ingestion provenance.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_science_status', 'scpc_science_status_shortcode');


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


function scpc_developer_portal_shortcode() {
    $base = untrailingslashit(get_option(SCPC_OPTION_BACKEND_URL, ''));
    if (!$base) {
        return '<div class="scpc-card scpc-error">Platform Core backend URL is not configured.</div>';
    }

    return '<section class="scpc-card">' .
        '<p class="scpc-kicker">Unified Public API</p>' .
        '<h3>Sustainable Catalyst Developer Portal</h3>' .
        '<p>Explore the public API, test requests, download SDKs and OpenAPI assets, review scopes and quotas, and configure signed webhooks.</p>' .
        '<a class="scpc-button" href="' . esc_url($base . '/developers') . '" target="_blank" rel="noopener">Open Developer Portal</a>' .
        '</section>';
}
add_shortcode('sc_developer_portal', 'scpc_developer_portal_shortcode');

function scpc_public_api_plans_shortcode() {
    $plans = scpc_api_get('/developers/plans.json');
    if (is_wp_error($plans)) {
        return '<div class="scpc-card scpc-error"><strong>API plans unavailable</strong><p>' .
            esc_html($plans->get_error_message()) .
            '</p></div>';
    }

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Developer access</p>
        <h3>Unified Public API Plans</h3>
        <div class="scpc-api-plan-grid">
            <?php foreach ($plans as $plan) : ?>
                <article class="scpc-api-plan">
                    <strong><?php echo esc_html($plan['name']); ?></strong>
                    <?php if (!empty($plan['description'])) : ?>
                        <p><?php echo esc_html($plan['description']); ?></p>
                    <?php endif; ?>
                    <p class="scpc-meta">
                        <?php echo esc_html(number_format_i18n(intval($plan['requests_per_minute']))); ?> requests/minute ·
                        <?php echo esc_html(number_format_i18n(intval($plan['requests_per_day']))); ?> requests/day ·
                        page size <?php echo esc_html(number_format_i18n(intval($plan['max_page_size']))); ?>
                    </p>
                </article>
            <?php endforeach; ?>
        </div>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_public_api_plans', 'scpc_public_api_plans_shortcode');


function scpc_trust_center_shortcode() {
    $base = untrailingslashit(get_option(SCPC_OPTION_BACKEND_URL, ''));
    if (!$base) {
        return '<div class="scpc-card scpc-error">Platform Core backend URL is not configured.</div>';
    }

    return '<section class="scpc-card">' .
        '<p class="scpc-kicker">Evaluation and public accountability</p>' .
        '<h3>Sustainable Catalyst Trust Center</h3>' .
        '<p>Review evaluation results, check-level evidence, incidents, known limitations, attestations, and machine-readable trust status.</p>' .
        '<a class="scpc-button" href="' . esc_url($base . '/trust') . '" target="_blank" rel="noopener">Open Trust Center</a>' .
        '</section>';
}
add_shortcode('sc_trust_center', 'scpc_trust_center_shortcode');

function scpc_trust_status_shortcode() {
    $status = scpc_api_get('/trust/status.json');
    if (is_wp_error($status)) {
        return '<div class="scpc-card scpc-error"><strong>Trust status unavailable</strong><p>' .
            esc_html($status->get_error_message()) .
            '</p></div>';
    }

    $overall = sanitize_html_class($status['overall_status']);
    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Public trust status</p>
        <h3>Sustainable Catalyst Platform Core</h3>
        <p>
            <span class="scpc-trust-status scpc-trust-<?php echo esc_attr($overall); ?>">
                <?php echo esc_html(ucfirst($status['overall_status'])); ?>
            </span>
            · <strong>Score:</strong> <?php echo is_null($status['overall_score']) ? 'N/A' : esc_html(number_format_i18n(floatval($status['overall_score']), 1)); ?>
            · <strong>Grade:</strong> <?php echo esc_html($status['grade']); ?>
            · <strong>Ledger:</strong> <?php echo !empty($status['ledger_valid']) ? 'Verified' : 'Failed'; ?>
        </p>
        <p class="scpc-meta">
            <?php echo esc_html(count($status['domains'])); ?> evaluation domains ·
            <?php echo esc_html(intval($status['open_findings'])); ?> open findings ·
            <?php echo esc_html(count($status['active_incidents'])); ?> active incidents ·
            <?php echo esc_html(count($status['known_limitations'])); ?> known limitations
        </p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_trust_status', 'scpc_trust_status_shortcode');


function scpc_dossier_center_shortcode() {
    $base = untrailingslashit(get_option(SCPC_OPTION_BACKEND_URL, ''));
    if (!$base) {
        return '<div class="scpc-card scpc-error">Platform Core backend URL is not configured.</div>';
    }
    return '<section class="scpc-card">' .
        '<p class="scpc-kicker">End-to-end decision records</p>' .
        '<h3>Sustainable Catalyst Signature Dossiers</h3>' .
        '<p>Inspect finalized evidence, workflow, trust, approval, and signature packages with machine-verifiable hashes.</p>' .
        '<a class="scpc-button" href="' . esc_url($base . '/dossier-center') . '" target="_blank" rel="noopener">Open Dossier Center</a>' .
        '</section>';
}
add_shortcode('sc_dossier_center', 'scpc_dossier_center_shortcode');

function scpc_signature_dossier_shortcode($atts) {
    $atts = shortcode_atts(['id' => ''], $atts, 'sc_signature_dossier');
    $dossier_id = sanitize_text_field($atts['id']);
    if (!$dossier_id) {
        return '<div class="scpc-card scpc-error">Dossier ID is required.</div>';
    }
    $dossier = scpc_api_get('/public/dossiers/' . rawurlencode($dossier_id));
    $verification = scpc_api_get('/public/dossiers/' . rawurlencode($dossier_id) . '/verify');
    if (is_wp_error($dossier) || is_wp_error($verification)) {
        $error = is_wp_error($dossier) ? $dossier : $verification;
        return '<div class="scpc-card scpc-error"><strong>Dossier unavailable</strong><p>' . esc_html($error->get_error_message()) . '</p></div>';
    }
    $valid = !empty($verification['valid']);
    ob_start(); ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Signature dossier</p>
        <h3><?php echo esc_html($dossier['title']); ?></h3>
        <p><?php echo esc_html($dossier['purpose']); ?></p>
        <p><strong>Signature:</strong> <span class="<?php echo $valid ? 'scpc-ledger-valid' : 'scpc-ledger-invalid'; ?>"><?php echo $valid ? 'Verified' : 'Failed'; ?></span> · <strong>Records:</strong> <?php echo esc_html(count($dossier['records'])); ?> · <strong>Approvals:</strong> <?php echo esc_html(count($dossier['approvals'])); ?></p>
        <p class="scpc-meta">Hash: <code><?php echo esc_html($dossier['dossier_hash']); ?></code><br />Signed by <?php echo esc_html($dossier['signed_by']); ?> using <?php echo esc_html($dossier['signature_algorithm']); ?></p>
    </section>
    <?php return ob_get_clean();
}
add_shortcode('sc_signature_dossier', 'scpc_signature_dossier_shortcode');

function scpc_workflow_status_shortcode($atts) {
    $atts = shortcode_atts(['id' => ''], $atts, 'sc_workflow_status');
    $run_id = sanitize_text_field($atts['id']);
    if (!$run_id) {
        return '<div class="scpc-card scpc-error">Workflow run ID is required.</div>';
    }
    $workflow = scpc_api_get('/v1/workflow-runs/' . rawurlencode($run_id));
    if (is_wp_error($workflow)) {
        return '<div class="scpc-card scpc-error"><strong>Workflow unavailable</strong><p>' . esc_html($workflow->get_error_message()) . '</p></div>';
    }
    $completed = 0;
    foreach ($workflow['steps'] as $step) { if (in_array($step['status'], ['completed', 'skipped'], true)) $completed++; }
    ob_start(); ?>
    <section class="scpc-card">
        <p class="scpc-kicker">End-to-end workflow</p>
        <h3><?php echo esc_html($workflow['title']); ?></h3>
        <p><strong>Status:</strong> <?php echo esc_html(ucwords(str_replace('_', ' ', $workflow['status']))); ?> · <strong>Progress:</strong> <?php echo esc_html($completed); ?>/<?php echo esc_html(count($workflow['steps'])); ?> stages</p>
        <?php if (!empty($workflow['current_step_key'])) : ?><p class="scpc-meta">Current stage: <code><?php echo esc_html($workflow['current_step_key']); ?></code></p><?php endif; ?>
    </section>
    <?php return ob_get_clean();
}
add_shortcode('sc_workflow_status', 'scpc_workflow_status_shortcode');

function scpc_economics_status_shortcode() {
    $stats = scpc_api_get('/v1/economics/stats');
    $health = scpc_api_get('/v1/live/connectors/health');

    if (is_wp_error($stats) || is_wp_error($health)) {
        $error = is_wp_error($stats) ? $stats : $health;
        return '<div class="scpc-card scpc-error"><strong>Economics connector pack unavailable</strong><p>' .
            esc_html($error->get_error_message()) .
            '</p></div>';
    }

    $economic_ids = [
        'imf.sdmx', 'oecd.sdmx', 'eurostat.statistics', 'ecb.sdmx',
        'bis.sdmx', 'bea.statistics', 'bls.timeseries', 'census.data',
        'sec.companyfacts', 'eia.v2-data', 'faostat.data', 'ilostat.sdmx',
    ];
    $configured = 0;
    if (!empty($health['connectors']) && is_array($health['connectors'])) {
        foreach ($health['connectors'] as $connector) {
            if (in_array($connector['id'] ?? '', $economic_ids, true) &&
                ($connector['configuration_status'] ?? '') === 'configured') {
                $configured++;
            }
        }
    }

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Free official statistics</p>
        <h3>Economics and Official Statistics Connector Pack</h3>
        <p>
            <strong>Configured connectors:</strong> <?php echo esc_html(number_format_i18n($configured)); ?>/12 ·
            <strong>Normalized records:</strong> <?php echo esc_html(number_format_i18n(intval($stats['records'] ?? 0))); ?> ·
            <strong>Public records:</strong> <?php echo esc_html(number_format_i18n(intval($stats['public_records'] ?? 0))); ?>
        </p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_economics_status', 'scpc_economics_status_shortcode');
