<?php
/**
 * Plugin Name: Sustainable Catalyst Platform Core
 * Description: WordPress connector for Sustainable Catalyst Platform Core registry, graph, evidence, developer, gateway, free live-data, international-law, scientific-data, official-statistics, geospatial, time-series, STAC, map-layer, streaming, alerts, source-reliability, and operational-facility, humanitarian-access, essential-services, and country-evidence federation and reconciliation, and Earth/Ocean/Space scientific-service routing, cross-product exchange, distributed scale-control services, and governance/access/audit, production-certification/recovery, and observability/SLO production-operations services, plus incident-response, change-control, rollback-coordination, continuity, backup-verification, and disaster-recovery services.
 * Version: 2.20.0
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SCPC_VERSION', '2.20.0');
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
        <code>[sc_platform_core_integration_readiness]</code><br />
        <code>[sc_platform_core_live_data_status]</code><br />
        <code>[sc_platform_core_international_law_status]</code><br />
        <code>[sc_platform_core_science_status]</code><br />
        <code>[sc_platform_core_economics_status]</code><br />
        <code>[sc_platform_core_data_fabric_status]</code><br />
        <code>[sc_platform_core_reliability_status]</code><br />
        <code>[sc_platform_core_facility_registry_status]</code><br />
        <code>[sc_platform_core_humanitarian_status]</code><br />
        <code>[sc_platform_core_country_evidence_status country="PSE"]</code><br />
        <code>[sc_platform_core_scientific_fabric_status]</code><br />
        <code>[sc_platform_core_scale_status]</code><br />
        <code>[sc_platform_core_governance_status]</code><br />
        <code>[sc_platform_core_operations_status]</code><br />
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

    $ready = scpc_api_get('/ready');
    $stats = scpc_api_get('/v1/stats');
    $release_ready = (!is_wp_error($ready) && !empty($ready['ok']));
    $entities = (!is_wp_error($stats) && isset($stats['entities'])) ? intval($stats['entities']) : 0;
    $relationships = (!is_wp_error($stats) && isset($stats['relationships'])) ? intval($stats['relationships']) : 0;

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Shared knowledge infrastructure</p>
        <h3>Sustainable Catalyst Platform Core</h3>
        <p>
            <strong>Status:</strong> Online ·
            <strong>Readiness:</strong> <?php echo $release_ready ? 'Ready' : 'Blocked'; ?> ·
            <strong>Version:</strong> <?php echo esc_html($health['version']); ?> ·
            <strong>Entities:</strong> <?php echo esc_html(number_format_i18n($entities)); ?> ·
            <strong>Relationships:</strong> <?php echo esc_html(number_format_i18n($relationships)); ?>
        </p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_status', 'scpc_status_shortcode');

function scpc_integration_readiness_shortcode() {
    $readiness = scpc_api_get('/integration/readiness');
    if (is_wp_error($readiness)) {
        return '<div class="scpc-card scpc-error"><strong>Platform integration readiness unavailable</strong><p>' .
            esc_html($readiness->get_error_message()) .
            '</p></div>';
    }

    $ready = !empty($readiness['ok']);
    $overall = isset($readiness['overall_status']) ? sanitize_text_field($readiness['overall_status']) : 'unknown';
    $required = isset($readiness['required_service_count']) ? intval($readiness['required_service_count']) : 0;
    $required_ready = isset($readiness['required_ready_count']) ? intval($readiness['required_ready_count']) : 0;
    $blockers = isset($readiness['required_blockers']) && is_array($readiness['required_blockers'])
        ? array_map('sanitize_text_field', $readiness['required_blockers'])
        : [];

    ob_start();
    ?>
    <section class="scpc-card <?php echo $ready ? '' : 'scpc-error'; ?>">
        <p class="scpc-kicker">Production integration readiness</p>
        <h3>Platform Core service fabric</h3>
        <p>
            <strong>Release readiness:</strong> <?php echo $ready ? 'Ready' : 'Blocked'; ?> ·
            <strong>Gateway:</strong> <?php echo esc_html(ucwords(str_replace('_', ' ', $overall))); ?> ·
            <strong>Required services:</strong> <?php echo esc_html($required_ready . '/' . $required); ?> ready
        </p>
        <?php if (!$ready && $blockers) : ?>
            <p class="scpc-meta"><strong>Blocking integrations:</strong> <?php echo esc_html(implode(', ', $blockers)); ?></p>
        <?php endif; ?>
        <p class="scpc-meta">Liveness and deployment readiness are evaluated separately. Service URLs and service tokens are never exposed by this status surface.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_integration_readiness', 'scpc_integration_readiness_shortcode');


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


function scpc_facility_registry_status_shortcode() {
    $status = scpc_api_get('/v1/facilities/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-card scpc-error"><strong>Facility Registry unavailable</strong><p>' .
            esc_html($status->get_error_message()) . '</p></div>';
    }
    $facilities = isset($status['facilities']) ? intval($status['facilities']) : 0;
    $observations = isset($status['observations']) ? intval($status['observations']) : 0;
    ob_start(); ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Operational evidence infrastructure</p>
        <h3>Facility Registry</h3>
        <p><strong>Status:</strong> <?php echo esc_html(ucfirst($status['status'] ?? 'unknown')); ?> ·
        <strong>Facilities:</strong> <?php echo esc_html(number_format_i18n($facilities)); ?> ·
        <strong>Observations:</strong> <?php echo esc_html(number_format_i18n($observations)); ?></p>
        <p class="scpc-meta">Facility identity is separate from dated operational, damage, access, service, capacity, and supply observations. Missing evidence is not interpreted as normal operation.</p>
    </section>
    <?php return ob_get_clean();
}
add_shortcode('sc_platform_core_facility_registry_status', 'scpc_facility_registry_status_shortcode');

function scpc_humanitarian_status_shortcode() {
    $status = scpc_api_get('/v1/humanitarian/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-card scpc-error"><strong>Humanitarian evidence fabric unavailable</strong><p>' .
            esc_html($status->get_error_message()) . '</p></div>';
    }
    $records = isset($status['records']) ? intval($status['records']) : 0;
    ob_start(); ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Humanitarian and essential-service evidence</p>
        <h3>Humanitarian Access & Essential Services Fabric</h3>
        <p><strong>Status:</strong> <?php echo esc_html(ucfirst($status['status'] ?? 'unknown')); ?> ·
        <strong>Records:</strong> <?php echo esc_html(number_format_i18n($records)); ?> ·
        <strong>Structured materialization:</strong> <?php echo !empty($status['auto_materialize_structured_observations']) ? 'Enabled' : 'Disabled'; ?></p>
        <p class="scpc-meta">Operational conditions, humanitarian indicators, classifications and structural baselines remain distinct. Missing records are not interpreted as normal conditions, and Core does not create synthetic crisis-severity or legal conclusions.</p>
    </section>
    <?php return ob_get_clean();
}
add_shortcode('sc_platform_core_humanitarian_status', 'scpc_humanitarian_status_shortcode');


function scpc_country_evidence_status_shortcode($atts) {
    $atts = shortcode_atts(['country' => 'PSE'], $atts, 'sc_platform_core_country_evidence_status');
    $country = strtoupper(sanitize_text_field($atts['country']));
    $status = scpc_api_get('/v1/country-evidence/readiness');
    $federation = scpc_api_get('/v1/country-evidence/country/' . rawurlencode($country) . '/federation');
    if (is_wp_error($status) || is_wp_error($federation)) {
        $error = is_wp_error($status) ? $status : $federation;
        return '<div class="scpc-card scpc-error"><strong>Country evidence federation unavailable</strong><p>' . esc_html($error->get_error_message()) . '</p></div>';
    }
    $records = isset($federation['records']) ? intval($federation['records']) : 0;
    $facilities = isset($federation['facilities']) ? intval($federation['facilities']) : 0;
    ob_start(); ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Country evidence federation</p>
        <h3><?php echo esc_html($country); ?> evidence hierarchy</h3>
        <p><strong>Status:</strong> <?php echo esc_html(ucfirst($status['status'] ?? 'unknown')); ?> ·
        <strong>Evidence records:</strong> <?php echo esc_html(number_format_i18n($records)); ?> ·
        <strong>Facilities:</strong> <?php echo esc_html(number_format_i18n($facilities)); ?></p>
        <p class="scpc-meta">Primary official, operational, intergovernmental and harmonized benchmark evidence remain separate. Core does not automatically average source disagreements or substitute subnational conditions for national statistics.</p>
    </section>
    <?php return ob_get_clean();
}
add_shortcode('sc_platform_core_country_evidence_status', 'scpc_country_evidence_status_shortcode');


function scpc_scientific_fabric_status_shortcode() {
    $status = scpc_api_get('/v1/scientific-fabric/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-card scpc-error"><strong>Scientific service fabric unavailable</strong><p>' .
            esc_html($status->get_error_message()) . '</p></div>';
    }
    $summaries = isset($status['domain_summaries']) && is_array($status['domain_summaries']) ? $status['domain_summaries'] : [];
    $earth = isset($summaries['earth']['records']) ? intval($summaries['earth']['records']) : 0;
    $ocean = isset($summaries['ocean']['records']) ? intval($summaries['ocean']['records']) : 0;
    $space = isset($summaries['space']['records']) ? intval($summaries['space']['records']) : 0;
    ob_start(); ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Scientific service routing</p>
        <h3>Earth · Ocean · Space</h3>
        <p><strong>Status:</strong> <?php echo esc_html(ucfirst($status['status'] ?? 'unknown')); ?> ·
        <strong>Earth:</strong> <?php echo esc_html(number_format_i18n($earth)); ?> ·
        <strong>Ocean:</strong> <?php echo esc_html(number_format_i18n($ocean)); ?> ·
        <strong>Space:</strong> <?php echo esc_html(number_format_i18n($space)); ?></p>
        <p class="scpc-meta">Domain bindings are navigation and service-routing metadata only. They do not modify source records, create scientific observations, or carry factual Truth precedence.</p>
    </section>
    <?php return ob_get_clean();
}
add_shortcode('sc_platform_core_scientific_fabric_status', 'scpc_scientific_fabric_status_shortcode');

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


function scpc_data_fabric_status_shortcode() {
    $stats = scpc_api_get('/v1/fabric/stats');
    $capabilities = scpc_api_get('/v1/fabric/capabilities');

    if (is_wp_error($stats) || is_wp_error($capabilities)) {
        $error = is_wp_error($stats) ? $stats : $capabilities;
        return '<div class="scpc-card scpc-error"><strong>Data fabric unavailable</strong><p>' .
            esc_html($error->get_error_message()) .
            '</p></div>';
    }

    $postgis_mode = isset($stats['postgis_mode']) ? sanitize_text_field($stats['postgis_mode']) : 'unknown';
    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Geospatial and scientific data infrastructure</p>
        <h3>Geospatial, Time-Series, and Scientific Data Fabric</h3>
        <p>
            <strong>Version:</strong> <?php echo esc_html(SCPC_VERSION); ?> ·
            <strong>Spatial mode:</strong> <?php echo esc_html(ucwords(str_replace('_', ' ', $postgis_mode))); ?> ·
            <strong>Features:</strong> <?php echo esc_html(number_format_i18n(intval($stats['geospatial_features'] ?? 0))); ?> ·
            <strong>Time series:</strong> <?php echo esc_html(number_format_i18n(intval($stats['time_series'] ?? 0))); ?> ·
            <strong>Points:</strong> <?php echo esc_html(number_format_i18n(intval($stats['time_series_points'] ?? 0))); ?> ·
            <strong>Assets:</strong> <?php echo esc_html(number_format_i18n(intval($stats['scientific_assets'] ?? 0))); ?> ·
            <strong>STAC items:</strong> <?php echo esc_html(number_format_i18n(intval($stats['stac_items'] ?? 0))); ?>
        </p>
        <p class="scpc-meta">GeoJSON, STAC, WMS/WMTS handoffs, COG, PMTiles, FITS, NetCDF, Zarr, GeoParquet, SDMX, and TAP/ADQL capabilities are source-aware and license-preserving.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_data_fabric_status', 'scpc_data_fabric_status_shortcode');


function scpc_reliability_status_shortcode() {
    $status = scpc_api_get('/v1/reliability/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-card scpc-error"><strong>Reliability plane unavailable</strong><p>' .
            esc_html($status->get_error_message()) .
            '</p></div>';
    }

    ob_start();
    ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Streaming and source reliability</p>
        <h3>Connector Reliability Control Plane</h3>
        <p>
            <strong>Release:</strong> <?php echo esc_html($status['release'] ?? SCPC_VERSION); ?> ·
            <strong>Streaming:</strong> <?php echo !empty($status['streaming_enabled']) ? 'Enabled' : 'Disabled'; ?> ·
            <strong>Worker:</strong> <?php echo !empty($status['worker_enabled']) ? 'Enabled' : 'Disabled'; ?> ·
            <strong>Failover:</strong> <?php echo !empty($status['provider_failover_enabled']) ? 'Enabled' : 'Disabled'; ?>
        </p>
        <p>
            <strong>Pending work:</strong> <?php echo esc_html(number_format_i18n(intval($status['pending_work_items'] ?? 0))); ?> ·
            <strong>Open dead letters:</strong> <?php echo esc_html(number_format_i18n(intval($status['open_dead_letters'] ?? 0))); ?> ·
            <strong>Stale connectors:</strong> <?php echo esc_html(number_format_i18n(intval($status['stale_connectors'] ?? 0))); ?>
        </p>
        <p class="scpc-meta">External provider health is observable but does not independently block Core release readiness.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('sc_platform_core_reliability_status', 'scpc_reliability_status_shortcode');


function scpc_exchange_status_shortcode() {
    $base = rtrim(get_option('scpc_api_base', ''), '/');
    if (!$base) {
        return '<div class="scpc-status scpc-status-unconfigured"><strong>Cross-Product Evidence Exchange</strong><br>Core endpoint not configured.</div>';
    }
    $response = wp_remote_get($base . '/v1/exchange/readiness', array('timeout' => 8));
    if (is_wp_error($response)) {
        return '<div class="scpc-status scpc-status-degraded"><strong>Cross-Product Evidence Exchange</strong><br>Readiness unavailable.</div>';
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    $status = isset($body['status']) ? esc_html($body['status']) : 'unknown';
    return '<div class="scpc-status"><strong>Cross-Product Evidence Exchange</strong><br>' . $status . ' · reference-first · non-destructive</div>';
}
add_shortcode('sc_platform_core_exchange_status', 'scpc_exchange_status_shortcode');


function scpc_scale_status_shortcode() {
    $response = scpc_api_get('/v1/scale/readiness');
    if (is_wp_error($response)) { return '<div class="scpc-status scpc-status--error">Scale control plane unavailable.</div>'; }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($body)) { return '<div class="scpc-status scpc-status--error">Scale status unavailable.</div>'; }
    $bp = !empty($body['backpressure']) ? 'Backpressure active' : 'Capacity available';
    return '<div class="scpc-status"><strong>Distributed Processing &amp; Scale</strong><br />' . esc_html($bp) . ' · queued ' . intval($body['queued_partitions'] ?? 0) . ' · active jobs ' . intval($body['active_jobs'] ?? 0) . '</div>';
}
add_shortcode('sc_platform_core_scale_status', 'scpc_scale_status_shortcode');


function scpc_governance_status_shortcode() {
    $response = scpc_api_get('/v1/governance/readiness');
    if (is_wp_error($response)) {
        return '<div class="scpc-status scpc-status--error">Governance control plane unavailable.</div>';
    }
    $status = esc_html($response['status'] ?? 'unknown');
    $mode = esc_html($response['enforcement_mode'] ?? 'unknown');
    $chain = esc_html($response['audit_chain'] ?? 'unknown');
    return '<div class="scpc-status"><strong>Governance:</strong> ' . $status . ' &middot; Enforcement: ' . $mode . ' &middot; Audit: ' . $chain . '</div>';
}
add_shortcode('sc_platform_core_governance_status', 'scpc_governance_status_shortcode');


add_shortcode('sc_platform_core_certification_status', function () {
    $base = rtrim((string) get_option('scpc_core_url', ''), '/');
    if (!$base) return '<div class="scpc-status">Core certification status unavailable: Core URL not configured.</div>';
    $response = wp_remote_get($base . '/api/v1/certification/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Core certification status unavailable.</div>';
    $payload = json_decode(wp_remote_retrieve_body($response), true);
    $data = isset($payload['data']) ? $payload['data'] : array();
    $state = (!empty($data['zero_pending_migrations'])) ? 'Migration Ready' : 'Migration Attention Required';
    return '<div class="scpc-status"><strong>Core Production Certification</strong><br>' . esc_html($state) . ' · Schema ' . esc_html(isset($data['schema_head']) ? $data['schema_head'] : 'unknown') . '</div>';
});


function scpc_observability_status_shortcode() {
    $response = scpc_api_get('/v1/observability/readiness');
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status--error">Core observability status unavailable.</div>';
    $status = esc_html($response['status'] ?? 'unknown');
    $samples = intval($response['metric_samples'] ?? 0);
    $slos = intval($response['active_slos'] ?? 0);
    $release = esc_html($response['latest_deployment_release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>Core Observability &amp; SLOs</strong><br />' . $status . ' · release ' . $release . ' · ' . $slos . ' SLOs · ' . $samples . ' metric samples</div>';
}
add_shortcode('sc_platform_core_observability_status', 'scpc_observability_status_shortcode');
function scpc_operations_status_shortcode() {
    $status = scpc_api_get('/v1/operations/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-card scpc-error"><strong>Platform operations status unavailable</strong><p>' . esc_html($status->get_error_message()) . '</p></div>';
    }
    $open = isset($status['open_incidents']) ? intval($status['open_incidents']) : 0;
    $changes = isset($status['active_changes']) ? intval($status['active_changes']) : 0;
    ob_start(); ?>
    <section class="scpc-card">
      <p class="scpc-kicker">Incident response & change control</p>
      <h3>Platform Operations</h3>
      <p><strong>Open incidents:</strong> <?php echo esc_html(number_format_i18n($open)); ?> · <strong>Active changes:</strong> <?php echo esc_html(number_format_i18n($changes)); ?> · <strong>Rollback:</strong> Operator-confirmed</p>
      <p class="scpc-meta">Automatic rollback and causal attribution from correlation are disabled.</p>
    </section><?php return ob_get_clean();
}
add_shortcode('sc_platform_core_operations_status', 'scpc_operations_status_shortcode');


function scpc_continuity_status_shortcode() {
    $status = scpc_api_get('/v1/continuity/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Core continuity status unavailable.</div>';
    $state = esc_html($status['state'] ?? 'unknown');
    $rpo = !empty($status['rpo_met']) ? 'RPO met' : 'RPO attention';
    $rto = !empty($status['rto_met']) ? 'RTO met' : 'RTO attention';
    return '<div class="scpc-status"><strong>Core Continuity &amp; Disaster Recovery</strong><br />' . $state . ' · ' . esc_html($rpo) . ' · ' . esc_html($rto) . '<br /><span class="scpc-meta">Backups remain operator-controlled; automatic database restore is disabled.</span></div>';
}
add_shortcode('sc_platform_core_continuity_status', 'scpc_continuity_status_shortcode');
