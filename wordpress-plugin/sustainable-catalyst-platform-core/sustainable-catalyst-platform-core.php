<?php
/**
 * Plugin Name: Sustainable Catalyst Platform Core
 * Description: WordPress connector for Sustainable Catalyst Platform Core registry, graph, evidence, developer, gateway, free live-data, international-law, scientific-data, official-statistics, geospatial, time-series, STAC, map-layer, streaming, alerts, source-reliability, and operational-facility, humanitarian-access, essential-services, and country-evidence federation and reconciliation, and Earth/Ocean/Space scientific-service routing, cross-product exchange, distributed scale-control services, and governance/access/audit, production-certification/recovery, and observability/SLO production-operations services, plus incident-response, change-control, rollback-coordination, continuity, backup-verification, disaster-recovery, and multi-region resilience/failover-coordination, and data-lifecycle/archival-integrity/preservation services, plus Federated Core trusted-node exchange services and capacity forecasting/resource-governance services, plus identity/credential/cryptographic-key lifecycle governance, distributed workload governance, and scientific object storage/processing adapter services, research object/model services, renderer-neutral visual reasoning object services, and visualization specification/renderer registry services, and governed System Maps and Flow Maps services, plus the renderer-neutral visual reasoning runtime/scene graph and analytical result/provenance integration.
 * Version: 3.48.0
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SCPC_VERSION', '3.48.0');
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
                            placeholder="https://core.sustainablecatalyst.com"
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
        <code>[sc_platform_core_continuity_status]</code><br />
        <code>[sc_platform_core_resilience_status]</code><br />
        <code>[sc_platform_core_lifecycle_status]</code><br />
        <code>[sc_platform_core_federation_status]</code><br />
        <code>[sc_platform_core_capacity_status]</code><br />
        <code>[sc_platform_core_credential_lifecycle_status]</code><br />
        <code>[sc_platform_core_workload_governance_status]</code><br />
        <code>[sc_platform_core_scientific_object_storage_status]</code><br />
        <code>[sc_platform_core_research_object_status]</code><br />
        <code>[sc_platform_core_visual_reasoning_status]</code><br />
        <code>[sc_platform_core_visual_runtime_status]</code><br />
        <code>[sc_platform_core_visualization_registry_status]</code><br />
        <code>[sc_platform_core_system_maps_status]</code><br />
        <code>[sc_platform_core_flow_maps_status]</code><br />
        <code>[sc_platform_core_scenario_landscapes_status]</code><br />
        <code>[sc_platform_core_model_canvas_status]</code><br />
        <code>[sc_platform_core_scenario_compute_status]</code><br />
        <code>[sc_platform_core_uncertainty_reasoning_status]</code><br />
        <code>[sc_platform_core_uncertainty_compute_status]</code><br />
        <code>[sc_platform_core_causal_systems_status]</code><br />
        <code>[sc_platform_core_analytical_runtime_status]</code><br />
        <code>[sc_platform_core_analytical_result_status]</code><br />
        <code>[sc_platform_core_statistical_reasoning_status]</code><br />
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


function scpc_resilience_status_shortcode() {
    $status = scpc_api_get('/v1/resilience/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Core resilience status unavailable.</div>';
    $state = esc_html($status['state'] ?? 'unknown');
    $groups = intval($status['failover_groups'] ?? 0);
    $blocked = intval($status['blocked_groups'] ?? 0);
    return '<div class="scpc-status"><strong>Core Multi-Region Resilience</strong><br />' . $state . ' · ' . $groups . ' failover groups · ' . $blocked . ' blocked<br /><span class="scpc-meta">Automatic failover is disabled; write failover requires replication safety.</span></div>';
}
add_shortcode('sc_platform_core_resilience_status', 'scpc_resilience_status_shortcode');

function scpc_lifecycle_status_shortcode() {
    $status = scpc_api_get('/v1/lifecycle/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Core preservation status unavailable.</div>';
    $state = esc_html($status['state'] ?? 'unknown');
    $archives = intval($status['archives'] ?? 0);
    $holds = intval($status['active_holds'] ?? 0);
    return '<div class="scpc-status"><strong>Core Data Lifecycle &amp; Preservation</strong><br />' . $state . ' · ' . $archives . ' archives · ' . $holds . ' active holds<br /><span class="scpc-meta">Hard delete is disabled; lifecycle actions preserve provenance and tombstone lineage.</span></div>';
}
add_shortcode('sc_platform_core_lifecycle_status', 'scpc_lifecycle_status_shortcode');


function scpc_federation_status_shortcode() {
    $status = scpc_api_get('/v1/federation/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Core federation status unavailable.</div>';
    $state = esc_html($status['state'] ?? 'unknown');
    $nodes = intval($status['trusted_nodes'] ?? 0);
    $refs = intval($status['remote_references'] ?? 0);
    return '<div class="scpc-status"><strong>Federated Core &amp; Trusted Node Exchange</strong><br />' . $state . ' · ' . $nodes . ' trusted nodes · ' . $refs . ' remote references<br /><span class="scpc-meta">Reference-first, authenticated, pull-based exchange. Automatic truth promotion and ownership transfer are disabled.</span></div>';
}
add_shortcode('sc_platform_core_federation_status', 'scpc_federation_status_shortcode');


function scpc_capacity_status_shortcode() {
    $status = scpc_api_get('/v1/capacity/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Core capacity status unavailable.</div>';
    $state = esc_html($status['state'] ?? 'unknown');
    $profiles = intval($status['resource_profiles'] ?? 0);
    $covered = intval($status['forecast_covered_profiles'] ?? 0);
    $critical = intval($status['critical_profiles'] ?? 0);
    $warning = intval($status['warning_profiles'] ?? 0);
    return '<div class="scpc-status"><strong>Capacity Forecasting &amp; Resource Governance</strong><br />' . $state . ' · ' . $covered . '/' . $profiles . ' forecast-covered · ' . $critical . ' critical · ' . $warning . ' warning<br /><span class="scpc-meta">Forecasts and soft limits are advisory. Automatic scaling, purchasing, deployment mutation, and hard admission control are disabled.</span></div>';
}
add_shortcode('sc_platform_core_capacity_status', 'scpc_capacity_status_shortcode');


function scpc_credential_lifecycle_status_shortcode() {
    $status = scpc_api_get('/v1/credentials/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Core credential lifecycle status unavailable.</div>';
    $state = esc_html($status['state'] ?? 'unknown');
    $tracked = intval($status['credential_records'] ?? 0);
    $expiring = intval($status['expiring_soon_versions'] ?? 0);
    $overdue = intval($status['overdue_rotations'] ?? 0);
    $compromised = intval($status['compromised_versions'] ?? 0);
    return '<div class="scpc-status"><strong>Credential &amp; Cryptographic Key Lifecycle</strong><br />' . $state . ' · ' . $tracked . ' tracked · ' . $expiring . ' expiring soon · ' . $overdue . ' overdue rotations · ' . $compromised . ' compromised<br /><span class="scpc-meta">Core stores lifecycle metadata and secret references only. Secret values and private-key material are not persisted; rotation remains operator-triggered.</span></div>';
}
add_shortcode('sc_platform_core_credential_lifecycle_status', 'scpc_credential_lifecycle_status_shortcode');


function scpc_workload_governance_status_shortcode() {
    $status = scpc_api_get('/v1/workload-governance/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Core workload governance status unavailable.</div>';
    $configured = !empty($status['configured']) ? 'configured' : 'unconfigured';
    $classes = intval($status['workload_classes'] ?? 0);
    $policies = intval($status['quota_policies'] ?? 0);
    $active = intval($status['active_leases'] ?? 0);
    return '<div class="scpc-status"><strong>Distributed Quotas &amp; Workload Governance</strong><br />' . esc_html($configured) . ' · ' . $classes . ' workload classes · ' . $policies . ' quota policies · ' . $active . ' active leases<br /><span class="scpc-meta">Database-shared quota state with auditable allow, throttle, and reject decisions. Automatic scaling and infrastructure purchasing remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_workload_governance_status', 'scpc_workload_governance_status_shortcode');


function scpc_scientific_object_storage_status_shortcode() {
    $status = scpc_api_get('/v1/scientific-objects/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Scientific object storage status unavailable.</div>';
    $stored = intval($status['stored_objects'] ?? 0);
    $adapters = intval($status['processing_adapters'] ?? 0);
    $executable = intval($status['executable_adapters'] ?? 0);
    $local = !empty($status['local_storage_ready']) ? 'local store ready' : 'local store attention';
    return '<div class="scpc-status"><strong>Scientific Object Storage &amp; Processing Adapters</strong><br />' . esc_html($local) . ' · ' . $stored . ' stored objects · ' . $adapters . ' adapters · ' . $executable . ' executable<br /><span class="scpc-meta">Credential-bearing references and arbitrary code execution are disabled. External scientific files remain provider-managed unless explicitly ingested.</span></div>';
}
add_shortcode('sc_platform_core_scientific_object_storage_status', 'scpc_scientific_object_storage_status_shortcode');

function scpc_research_object_status_shortcode() {
    $status = scpc_api_get('/v1/research-objects/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error">Research object and model foundation status unavailable.</div>';
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $projects = intval($counts['research-project'] ?? 0);
    $models = intval($counts['model'] ?? 0);
    $scenarios = intval($counts['scenario'] ?? 0);
    $runs = intval($counts['model-run'] ?? 0);
    return '<div class="scpc-status"><strong>Research Object &amp; Model Foundation</strong><br />' . $projects . ' projects · ' . $models . ' models · ' . $scenarios . ' scenarios · ' . $runs . ' model runs<br /><span class="scpc-meta">Core governs research identity, graph relationships, provenance, and reproducibility metadata. Model execution remains in Lab, Workbench, or an explicitly external executor.</span></div>';
}
add_shortcode('sc_platform_core_research_object_status', 'scpc_research_object_status_shortcode');


function scpc_visual_reasoning_status_shortcode() {
    $status = scpc_api_get('/v1/visual-reasoning/readiness');

    if (!is_wp_error($status)) {
        $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
        $objects = intval($counts['objects'] ?? 0);
        $elements = intval($counts['elements'] ?? 0);
        $relations = intval($counts['relations'] ?? 0);
        $snapshots = intval($counts['snapshots'] ?? 0);
        $renderer = !empty($status['renderer_neutral']) ? 'renderer-neutral' : 'renderer-attached';
        $release = isset($status['release']) ? sanitize_text_field((string) $status['release']) : SCPC_VERSION;

        return '<div class="scpc-status"><strong>Visual Reasoning Object Model</strong><br />' .
            $objects . ' visual objects · ' . $elements . ' elements · ' . $relations . ' relations · ' . $snapshots . ' snapshots<br />' .
            '<span class="scpc-meta">Core ' . esc_html($release) . ' · ' . esc_html($renderer) . ' semantic model. Core governs meaning, source bindings, uncertainty, caveats, and reproducible snapshots; v2.30 adds governed renderer contracts while renderer execution and layout execution remain external to Core.</span></div>';
    }

    // Some production reverse-proxy configurations expose /health while restricting
    // newer internal /v1 capability routes. Health carries the visual-reasoning
    // capability flag, so fail soft rather than reporting the feature offline.
    $health = scpc_api_get('/health');
    if (!is_wp_error($health) && !empty($health['visual_reasoning_object_model'])) {
        $release = isset($health['version']) ? sanitize_text_field((string) $health['version']) : SCPC_VERSION;
        $detail = '';
        if (current_user_can('manage_options')) {
            $detail = '<br /><span class="scpc-meta">Detailed readiness route unavailable: ' .
                esc_html($status->get_error_message()) . '</span>';
        }
        return '<div class="scpc-status"><strong>Visual Reasoning Object Model</strong><br />' .
            'Online · Core ' . esc_html($release) . '<br />' .
            '<span class="scpc-meta">Capability confirmed through Platform Core health. Detailed visual-object counts are temporarily unavailable through the WordPress connector.</span>' .
            $detail . '</div>';
    }

    $message = 'Visual reasoning object model status unavailable.';
    if (current_user_can('manage_options')) {
        $message .= ' ' . esc_html($status->get_error_message());
        if (is_wp_error($health)) {
            $message .= ' Health check: ' . esc_html($health->get_error_message());
        }
    }
    return '<div class="scpc-status scpc-status--error">' . $message . '</div>';
}
add_shortcode('sc_platform_core_visual_reasoning_status', 'scpc_visual_reasoning_status_shortcode');

function scpc_visualization_registry_status_shortcode() {
    $status = scpc_api_get('/v1/visualization/readiness');
    if (is_wp_error($status)) {
        $health = scpc_api_get('/health');
        $message = esc_html($status->get_error_message());
        if (is_wp_error($health)) {
            $message .= ' Health check: ' . esc_html($health->get_error_message());
        }
        return '<div class="scpc-status scpc-status--error"><strong>Visualization Specification &amp; Renderer Registry status unavailable.</strong><br /><span class="scpc-meta">' . $message . '</span></div>';
    }
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $specs = intval($counts['specifications'] ?? 0);
    $renderers = intval($counts['renderers'] ?? 0);
    $rules = intval($counts['compatibility_rules'] ?? 0);
    $resolutions = intval($counts['resolutions'] ?? 0);
    $release = sanitize_text_field($status['release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>Visualization Specification &amp; Renderer Registry</strong><br />' . $specs . ' specifications · ' . $renderers . ' renderer contracts · ' . $rules . ' compatibility rules · ' . $resolutions . ' resolutions<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed specification and compatibility metadata. Renderer execution, layout execution, and render-output generation remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_visualization_registry_status', 'scpc_visualization_registry_status_shortcode');




function scpc_system_maps_status_shortcode() {
    $status = scpc_api_get('/v1/system-maps/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-status scpc-status--error"><strong>System Maps status unavailable.</strong><br /><span class="scpc-meta">' . esc_html($status->get_error_message()) . '</span></div>';
    }
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $maps = intval($counts['system_maps'] ?? 0);
    $domains = intval($counts['domains'] ?? 0);
    $boundaries = intval($counts['boundaries'] ?? 0);
    $views = intval($counts['views'] ?? 0);
    $release = sanitize_text_field($status['release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>System Maps</strong><br />' . $maps . ' maps · ' . $domains . ' domains · ' . $boundaries . ' boundaries · ' . $views . ' saved views<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed system-map semantics and specification compilation. Layout and causal inference remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_system_maps_status', 'scpc_system_maps_status_shortcode');


function scpc_flow_maps_status_shortcode() {
    $status = scpc_api_get('/v1/flow-maps/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-status scpc-status--error"><strong>Flow Maps status unavailable.</strong><br /><span class="scpc-meta">' . esc_html($status->get_error_message()) . '</span></div>';
    }
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $maps = intval($counts['flow_maps'] ?? 0);
    $channels = intval($counts['channels'] ?? 0);
    $flows = intval($counts['flows'] ?? 0);
    $states = intval($counts['node_states'] ?? 0);
    $release = sanitize_text_field($status['release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>Flow Maps</strong><br />' . $maps . ' maps · ' . $channels . ' channels · ' . $flows . ' flows · ' . $states . ' node states<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · relation-bound directed-flow semantics and unit-safe summaries. Core does not convert units, simulate systems, or claim conservation automatically.</span></div>';
}
add_shortcode('sc_platform_core_flow_maps_status', 'scpc_flow_maps_status_shortcode');


function scpc_scenario_landscapes_status_shortcode() {
    $status = scpc_api_get('/v1/scenario-landscapes/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-status scpc-status--error"><strong>Scenario Landscapes status unavailable.</strong><br /><span class="scpc-meta">' . esc_html($status->get_error_message()) . '</span></div>';
    }
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $landscapes = intval($counts['landscapes'] ?? 0);
    $scenarios = intval($counts['scenarios'] ?? 0);
    $dimensions = intval($counts['dimensions'] ?? 0);
    $values = intval($counts['values'] ?? 0);
    $release = sanitize_text_field($status['release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>Scenario Landscapes</strong><br />' . $landscapes . ' landscapes · ' . $scenarios . ' scenarios · ' . $dimensions . ' dimensions · ' . $values . ' values<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed scenario comparison semantics, uncertainty-aware values, and reproducible visualization specifications. Scenario execution, ranking, and optimization remain external to Core.</span></div>';
}
add_shortcode('sc_platform_core_scenario_landscapes_status', 'scpc_scenario_landscapes_status_shortcode');


function scpc_model_canvas_status_shortcode() {
    $status = scpc_api_get('/v1/model-canvases/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-status scpc-status--error"><strong>Interactive Model Canvas status unavailable.</strong><br /><span class="scpc-meta">' . esc_html($status->get_error_message()) . '</span></div>';
    }
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $canvases = intval($counts['canvases'] ?? 0);
    $nodes = intval($counts['nodes'] ?? 0);
    $controls = intval($counts['controls'] ?? 0);
    $states = intval($counts['states'] ?? 0);
    $release = sanitize_text_field($status['release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>Interactive Model Canvas</strong><br />' . $canvases . ' canvases · ' . $nodes . ' nodes · ' . $controls . ' controls · ' . $states . ' saved states<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed model interaction semantics and external-execution handoffs. Numerical model execution and layout remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_model_canvas_status', 'scpc_model_canvas_status_shortcode');


function scpc_scenario_compute_status_shortcode() {
    $status = scpc_api_get('/v1/scenario-compute/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-status scpc-status--error"><strong>Scenario Compute Engine status unavailable.</strong><br /><span class="scpc-meta">' . esc_html($status->get_error_message()) . '</span></div>';
    }
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $plans = intval($counts['plans'] ?? 0);
    $cases = intval($counts['cases'] ?? 0);
    $requests = intval($counts['requests'] ?? 0);
    $bindings = intval($counts['result_bindings'] ?? 0);
    $release = sanitize_text_field($status['release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>Scenario Compute Engine</strong><br />' . $plans . ' plans · ' . $cases . ' cases · ' . $requests . ' execution requests · ' . $bindings . ' result bindings<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · reproducible scenario-compute orchestration and Lab/Workbench handoffs. Numerical execution and arbitrary code execution remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_scenario_compute_status', 'scpc_scenario_compute_status_shortcode');


function scpc_uncertainty_reasoning_status_shortcode() {
    $status = scpc_api_get('/v1/uncertainty-reasoning/readiness');
    if (is_wp_error($status)) {
        return '<div class="scpc-status scpc-status--error"><strong>Uncertainty, Sensitivity & Ensemble Reasoning status unavailable.</strong><br /><span class="scpc-meta">' . esc_html($status->get_error_message()) . '</span></div>';
    }
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $uncertainties = intval($counts['uncertainty_definitions'] ?? 0);
    $studies = intval($counts['sensitivity_studies'] ?? 0);
    $ensembles = intval($counts['ensembles'] ?? 0);
    $members = intval($counts['ensemble_members'] ?? 0);
    $release = sanitize_text_field($status['release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>Uncertainty, Sensitivity & Ensemble Reasoning</strong><br />' . $uncertainties . ' uncertainty definitions · ' . $studies . ' sensitivity studies · ' . $ensembles . ' ensembles · ' . $members . ' ensemble members<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed uncertainty semantics, externally supplied sensitivity measures, and ensemble provenance. Sampling, sensitivity algorithms, numerical execution, and ensemble aggregation remain external to Core.</span></div>';
}
add_shortcode('sc_platform_core_uncertainty_reasoning_status', 'scpc_uncertainty_reasoning_status_shortcode');


function scpc_uncertainty_compute_status_shortcode() {
    $status = scpc_api_get('/v1/uncertainty-compute/readiness');
    if (is_wp_error($status)) return '<div class="scpc-status scpc-status--error"><strong>Uncertainty Compute Runtime status unavailable.</strong><br /><span class="scpc-meta">' . esc_html($status->get_error_message()) . '</span></div>';
    $counts = isset($status['counts']) && is_array($status['counts']) ? $status['counts'] : [];
    $runs = intval($counts['compute_runs'] ?? 0); $release = sanitize_text_field($status['release'] ?? SCPC_VERSION);
    return '<div class="scpc-status"><strong>Uncertainty Compute Runtime</strong><br />' . $runs . ' compute runs<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · deterministic Monte Carlo/LHS sampling, Sobol/Morris analysis helpers, ensemble statistics, empirical probability estimation, and governed Lab/Workbench handoffs. Arbitrary model execution and automatic truth promotion remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_uncertainty_compute_status', 'scpc_uncertainty_compute_status_shortcode');

// v2.37.0.2 Causal Systems Explorer
function scpc_causal_systems_status_shortcode() {
    $status = scpc_api_get('/v1/causal-systems/readiness');
    if (!is_array($status)) { return '<div class="scpc-status"><strong>Causal Systems Explorer</strong><br /><span class="scpc-meta">Status unavailable.</span></div>'; }
    $counts = $status['counts'] ?? array();
    $release = $status['release'] ?? SCPC_VERSION;
    return '<div class="scpc-status"><strong>Causal Systems Explorer</strong><br />' . intval($counts['graphs'] ?? 0) . ' graphs · ' . intval($counts['variables'] ?? 0) . ' variables · ' . intval($counts['edges'] ?? 0) . ' edges · ' . intval($counts['estimates'] ?? 0) . ' estimates<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed causal graphs, interventions, explicit identification assumptions, diagnostics, and attributable effect estimates. Structural graph reasoning is deterministic; causal identification and effect estimation are never silently inferred.</span></div>';
}
add_shortcode('sc_platform_core_causal_systems_status', 'scpc_causal_systems_status_shortcode');


// v2.38.0 Spatial & Temporal Visual Reasoning
function scpc_spatial_temporal_status_shortcode() {
    $status = scpc_api_get('/v1/spatial-temporal/readiness');
    if (!is_array($status)) { return '<div class="scpc-status"><strong>Spatial & Temporal Visual Reasoning</strong><br /><span class="scpc-meta">Status unavailable.</span></div>'; }
    $counts = $status['counts'] ?? array(); $release = $status['release'] ?? SCPC_VERSION;
    return '<div class="scpc-status"><strong>Spatial & Temporal Visual Reasoning</strong><br />' . intval($counts['scenes'] ?? 0) . ' scenes · ' . intval($counts['features'] ?? 0) . ' features · ' . intval($counts['events'] ?? 0) . ' events · ' . intval($counts['trajectories'] ?? 0) . ' trajectories<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed spatial-temporal scenes, GeoJSON feature bindings, events, trajectories, change observations, and renderer-neutral map/timeline specifications. GIS, raster, remote-sensing, and temporal model execution remain external to Core.</span></div>';
}
add_shortcode('sc_platform_core_spatial_temporal_status', 'scpc_spatial_temporal_status_shortcode');


// v2.39.0 Research Librarian Visual Explanation
function scpc_research_visual_explanation_status_shortcode() {
    $status = scpc_api_get('/v1/research-visual-explanations/readiness');
    if (!is_array($status)) { return '<div class="scpc-status"><strong>Research Librarian Visual Explanation</strong><br /><span class="scpc-meta">Status unavailable.</span></div>'; }
    $counts = $status['counts'] ?? array(); $release = $status['release'] ?? SCPC_VERSION;
    return '<div class="scpc-status"><strong>Research Librarian Visual Explanation</strong><br />' . intval($counts['explanations'] ?? 0) . ' explanations · ' . intval($counts['nodes'] ?? 0) . ' nodes · ' . intval($counts['relations'] ?? 0) . ' relations · ' . intval($counts['citations'] ?? 0) . ' citations<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed, citation-aware research explanation graphs, evidence bindings, saved views, immutable snapshots, and renderer-neutral visual contracts. Retrieval, prose generation, citation selection, source ranking, and rendering remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_research_visual_explanation_status', 'scpc_research_visual_explanation_status_shortcode');


// v2.41.0 Cross-Product Visual Research Objects
function scpc_cross_product_visual_research_status_shortcode() {
    $status = scpc_api_get('/v1/cross-product-visual-research/readiness');
    if (!is_array($status)) { return '<div class="scpc-status"><strong>Cross-Product Visual Research Objects</strong><br /><span class="scpc-meta">Status unavailable.</span></div>'; }
    $counts = $status['counts'] ?? array(); $release = $status['release'] ?? SCPC_VERSION;
    return '<div class="scpc-status"><strong>Cross-Product Visual Research Objects</strong><br />' . intval($counts['objects'] ?? 0) . ' objects · ' . intval($counts['members'] ?? 0) . ' members · ' . intval($counts['relations'] ?? 0) . ' relations · ' . intval($counts['snapshots'] ?? 0) . ' snapshots<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed cross-product semantic packages with explicit product identity, provenance-aware member references, cross-product relations, saved composite views, immutable snapshots, and renderer-neutral portability. Remote fetching, model/analysis execution, truth merging, layout, and rendering remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_cross_product_visual_research_status', 'scpc_cross_product_visual_research_status_shortcode');


// v2.41.0 Reproducible Visual Knowledge Layer
function scpc_reproducible_visual_knowledge_status_shortcode() {
    $status = scpc_api_get('/v1/reproducible-visual-knowledge/readiness');
    if (!is_array($status)) { return '<div class="scpc-status"><strong>Reproducible Visual Knowledge Layer</strong><br /><span class="scpc-meta">Status unavailable.</span></div>'; }
    $counts = $status['counts'] ?? array(); $release = $status['release'] ?? SCPC_VERSION;
    return '<div class="scpc-status"><strong>Reproducible Visual Knowledge Layer</strong><br />' . intval($counts['packages'] ?? 0) . ' packages · ' . intval($counts['inputs'] ?? 0) . ' locked inputs · ' . intval($counts['replay_plans'] ?? 0) . ' replay plans · ' . intval($counts['verifications'] ?? 0) . ' verifications<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · versioned input manifests, environment capture, external-only replay plans, integrity fingerprints, verification evidence, immutable snapshots, and portable reproducibility packages. Specialist execution, arbitrary code execution, output-equivalence claims without external evidence, and truth promotion remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_reproducible_visual_knowledge_status', 'scpc_reproducible_visual_knowledge_status_shortcode');


// v2.42.0 Open Forensics — Forensic Object Model & Evidence Provenance
function scpc_open_forensics_status_shortcode() {
    $status = scpc_api_get('/v1/open-forensics/readiness');
    if (!is_array($status)) { return '<div class="scpc-status"><strong>Open Forensics</strong><br /><span class="scpc-meta">Status unavailable.</span></div>'; }
    $counts = $status['counts'] ?? array(); $release = $status['release'] ?? SCPC_VERSION;
    return '<div class="scpc-status"><strong>Open Forensics — Evidence Provenance</strong><br />' . intval($counts['investigations'] ?? 0) . ' investigations · ' . intval($counts['objects'] ?? 0) . ' forensic objects · ' . intval($counts['evidence_items'] ?? 0) . ' evidence items · ' . intval($counts['provenance_activities'] ?? 0) . ' provenance activities<br /><span class="scpc-meta">Core ' . esc_html($release) . ' · governed forensic objects, source/evidence bindings, provenance, custody integrity, claims, contradictions, competing hypotheses, and immutable snapshots. Authenticity, identity attribution, automated truth determination, hypothesis ranking, verdicts, and legal conclusions remain outside Core.</span></div>';
}
add_shortcode('sc_platform_core_open_forensics_status', 'scpc_open_forensics_status_shortcode');


// v2.45.0 Open Forensics — Evidence Integrity & Chain of Custody
function scpc_custody_integrity_status_shortcode() {
    $url = rtrim(SCPC_CORE_BASE, '/') . '/v1/open-forensics/readiness';
    $response = wp_remote_get($url, array('timeout' => 8));
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status-error">Open Forensics custody status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status scpc-status-error">Open Forensics custody status unavailable.</div>';
    $ready = !empty($data['migration_0047_applied']) && !empty($data['chain_of_custody_recording_by_core']) && !empty($data['evidence_integrity_verification_by_core']);
    return '<div class="scpc-status"><strong>Evidence Integrity &amp; Chain of Custody:</strong> ' . ($ready ? 'Ready' : 'Not ready') . ' · Core ' . esc_html($data['release'] ?? 'unknown') . '</div>';
}
add_shortcode('sc_platform_core_custody_integrity_status', 'scpc_custody_integrity_status_shortcode');


// v2.45.0 Open Forensics — Claims, Contradictions & Competing Hypotheses
function scpc_forensic_hypothesis_status_shortcode() {
    $status = scpc_api_get('/v1/open-forensics/readiness');
    if (!is_array($status)) return '<div class="scpc-status scpc-status-error">Open Forensics reasoning status unavailable.</div>';
    $counts = $status['counts'] ?? array(); $release = $status['release'] ?? SCPC_VERSION;
    $ready = !empty($status['migration_0048_applied']) && !empty($status['structured_claim_registry_by_core']) && !empty($status['competing_hypothesis_registry_by_core']);
    return '<div class="scpc-status"><strong>Claims, Contradictions &amp; Competing Hypotheses:</strong> ' . ($ready ? 'Ready' : 'Not ready') . ' · ' . intval($counts['claims'] ?? 0) . ' claims · ' . intval($counts['contradictions'] ?? 0) . ' contradictions · ' . intval($counts['hypotheses'] ?? 0) . ' hypotheses · Core ' . esc_html($release) . '</div>';
}
add_shortcode('sc_platform_core_forensic_hypothesis_status', 'scpc_forensic_hypothesis_status_shortcode');


// v2.45.0 Open Forensics — Forensic Timeline & Event Reconstruction
function scpc_forensic_timeline_status_shortcode() {
    $response = wp_remote_get(rtrim(SCPC_CORE_BASE, '/') . '/v1/open-forensics/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status-error">Open Forensics timeline status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status scpc-status-error">Open Forensics timeline status unavailable.</div>';
    $ready = !empty($data['migration_0049_applied']) && !empty($data['forensic_event_registry_by_core']) && !empty($data['reconstruction_hypothesis_registry_by_core']);
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Forensic Timeline &amp; Event Reconstruction ' . ($ready ? 'Ready' : 'Not Ready') . '</strong><br />' . intval($counts['events'] ?? 0) . ' events · ' . intval($counts['event_relations'] ?? 0) . ' event relations · ' . intval($counts['event_reconstructions'] ?? 0) . ' reconstruction hypotheses<br /><span class="scpc-meta">Core ' . esc_html($data['release'] ?? SCPC_VERSION) . ' · explicit evidence-linked timelines; reconstructed sequence remains a hypothesis, not an automated truth claim.</span></div>';
}
add_shortcode('sc_platform_core_forensic_timeline_status', 'scpc_forensic_timeline_status_shortcode');


// v2.46.0 Open Forensics — Forensic Spatial/Temporal Evidence Integration
function scpc_forensic_spatial_temporal_status_shortcode() {
    $response = wp_remote_get(rtrim(SCPC_CORE_BASE, '/') . '/v1/open-forensics/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status-error">Open Forensics spatial/temporal status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status scpc-status-error">Open Forensics spatial/temporal status unavailable.</div>';
    $ready = !empty($data['migration_0050_applied']) && !empty($data['evidence_spatial_binding_by_core']) && !empty($data['linked_map_timeline_specification_by_core']);
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Forensic Spatial/Temporal Evidence Integration ' . ($ready ? 'Ready' : 'Not Ready') . '</strong><br />' . intval($counts['places'] ?? 0) . ' places · ' . intval($counts['trajectory_evidence'] ?? 0) . ' trajectories · ' . intval($counts['spatial_temporal_intersections'] ?? 0) . ' explicit intersections<br /><span class="scpc-meta">Core ' . esc_html($data['release'] ?? SCPC_VERSION) . ' · linked map/timeline evidence with Site Intelligence handoffs; Core does not perform spatial joins, reprojection, routing, or remote sensing.</span></div>';
}
add_shortcode('sc_platform_core_forensic_spatial_temporal_status', 'scpc_forensic_spatial_temporal_status_shortcode');

// v2.47.0 Open Forensics — Media Artifact & Derivative Provenance
function scpc_forensic_media_provenance_status_shortcode() {
    $response = wp_remote_get(rtrim(SCPC_CORE_BASE, '/') . '/v1/open-forensics/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status-error">Open Forensics media provenance status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status scpc-status-error">Open Forensics media provenance status unavailable.</div>';
    $ready = !empty($data['migration_0051_applied']) && !empty($data['media_artifact_registry_by_core']) && !empty($data['declared_derivative_lineage_by_core']);
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Media Artifact &amp; Derivative Provenance ' . ($ready ? 'Ready' : 'Not Ready') . '</strong><br />' . intval($counts['media_artifacts'] ?? 0) . ' media artifacts · ' . intval($counts['media_derivations'] ?? 0) . ' declared derivations · ' . intval($counts['media_comparisons'] ?? 0) . ' comparison records<br /><span class="scpc-meta">Core ' . esc_html($data['release'] ?? SCPC_VERSION) . ' · provenance and fingerprint records only; Core does not infer authenticity, manipulation intent, authorship, or derivative identity.</span></div>';
}
add_shortcode('sc_platform_core_forensic_media_provenance_status', 'scpc_forensic_media_provenance_status_shortcode');


// v2.48.0 Open Forensics — Quantitative Reconstruction & Reproduction Handoffs
function scpc_forensic_quantitative_reconstruction_status_shortcode() {
    $response = wp_remote_get(scpc_core_url('/v1/open-forensics/readiness'), array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status-error">Open Forensics quantitative reconstruction status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status scpc-status-error">Open Forensics quantitative reconstruction status unavailable.</div>';
    $ready = !empty($data['migration_0052_applied']) && !empty($data['quantitative_reconstruction_registry_by_core']) && !empty($data['workbench_lab_handoff_contracts_by_core']);
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Quantitative Reconstruction &amp; Reproduction Handoffs ' . ($ready ? 'Ready' : 'Not Ready') . '</strong><br />' . intval($counts['quantitative_reconstructions'] ?? 0) . ' reconstructions · ' . intval($counts['quantitative_handoffs'] ?? 0) . ' runtime handoffs · ' . intval($counts['quantitative_reproduction_packages'] ?? 0) . ' reproduction packages<br /><span class="scpc-meta">Core ' . esc_html($data['release'] ?? SCPC_VERSION) . ' · manifests and external-runtime handoffs only; Core does not execute quantitative models or promote outputs to truth.</span></div>';
}
add_shortcode('sc_platform_core_forensic_quantitative_reconstruction_status', 'scpc_forensic_quantitative_reconstruction_status_shortcode');


// v2.50.0 Open Forensics — Testimony, Statements & Documentary Evidence
function scpc_forensic_documentary_evidence_status_shortcode() {
    $response = wp_remote_get(scpc_core_url('/v1/open-forensics/readiness'), array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status-error">Open Forensics documentary evidence status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status scpc-status-error">Open Forensics documentary evidence status unavailable.</div>';
    $ready = !empty($data['migration_0053_applied']) && !empty($data['statement_testimony_registry_by_core']) && !empty($data['source_context_preservation_by_core']);
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Testimony, Statements &amp; Documentary Evidence ' . ($ready ? 'Ready' : 'Not Ready') . '</strong><br />' . intval($counts['statements'] ?? 0) . ' statements · ' . intval($counts['documents'] ?? 0) . ' documents · ' . intval($counts['document_assertions'] ?? 0) . ' documentary assertions<br /><span class="scpc-meta">Core ' . esc_html($data['release'] ?? SCPC_VERSION) . ' · source-context and analyst-declared relations only; Core does not verify identity/authorship, score credibility, or promote statements to truth.</span></div>';
}
add_shortcode('sc_platform_core_forensic_documentary_evidence_status', 'scpc_forensic_documentary_evidence_status_shortcode');


// v2.50.0 Open Forensics — Forensic Research Graph
function scpc_forensic_research_graph_status_shortcode() {
    $response = wp_remote_get(scpc_core_url('/v1/open-forensics/readiness'), array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status-error">Open Forensics research graph status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status scpc-status-error">Open Forensics research graph status unavailable.</div>';
    $ready = !empty($data['migration_0054_applied']) && !empty($data['forensic_research_graph_registry_by_core']) && !empty($data['cross_forensics_node_binding_by_core']);
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Forensic Research Graph ' . ($ready ? 'Ready' : 'Not Ready') . '</strong><br />' . intval($counts['research_graphs'] ?? 0) . ' graphs · ' . intval($counts['research_graph_nodes'] ?? 0) . ' nodes · ' . intval($counts['research_graph_edges'] ?? 0) . ' explicit edges<br /><span class="scpc-meta">Core ' . esc_html($data['release'] ?? SCPC_VERSION) . ' · cross-forensics references and explicit relations only; Core does not infer identity, causation, proof, or truth from graph topology.</span></div>';
}
add_shortcode('sc_platform_core_forensic_research_graph_status', 'scpc_forensic_research_graph_status_shortcode');


function scpc_reproducible_investigation_packages_status_shortcode() {
    $response = wp_remote_get(scpc_core_base_url() . '/v1/open-forensics/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status scpc-status-error">Reproducible Investigation Packages status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status scpc-status-error">Reproducible Investigation Packages status unavailable.</div>';
    $counts = is_array($data['counts'] ?? null) ? $data['counts'] : array();
    $ready = !empty($data['migration_0055_applied']) && !empty($data['reproducible_investigation_packages_by_core']);
    return '<div class="scpc-status"><strong>Reproducible Investigation Packages ' . ($ready ? 'Ready' : 'Not Ready') . '</strong><br />' . intval($counts['investigation_packages'] ?? 0) . ' packages · ' . intval($counts['investigation_package_components'] ?? 0) . ' frozen components · ' . intval($counts['investigation_package_verifications'] ?? 0) . ' verifications<br /><span class="scpc-meta">Core ' . esc_html($data['release'] ?? SCPC_VERSION) . ' · reproducibility and integrity verification do not determine authenticity, admissibility, causation, or truth.</span></div>';
}
add_shortcode('sc_platform_core_reproducible_investigation_packages_status', 'scpc_reproducible_investigation_packages_status_shortcode');


add_shortcode('sc_platform_core_predictive_intelligence_status', function () {
    $base = rtrim(get_option('scpc_core_base_url', 'https://core.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v1/predictive-intelligence/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Predictive Intelligence status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Predictive Intelligence status unavailable.</div>';
    $c = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Predictive Intelligence Online</strong><br>' .
      esc_html(($c['models'] ?? 0) . ' models · ' . ($c['forecast_runs'] ?? 0) . ' forecast runs · ' . ($c['forecast_observations'] ?? 0) . ' forecast observations') .
      '<br><small>Core records forecast provenance; fitting and inference remain specialist-runtime responsibilities.</small></div>';
});


add_shortcode('sc_platform_core_predictive_backtesting_status', function () {
    $base = rtrim((string) get_option(SCPC_OPTION_BACKEND_URL, ''), '/');
    if (!$base) return '<div class="scpc-status">Platform Core backend URL is not configured.</div>';
    $response = wp_remote_get($base . '/v1/predictive-intelligence/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Predictive backtesting status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Predictive backtesting status unavailable.</div>';
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Predictive Backtesting Online</strong><br>' .
      esc_html((string)($counts['time_series_datasets'] ?? 0)) . ' time-series datasets · ' .
      esc_html((string)($counts['backtest_plans'] ?? 0)) . ' backtest plans · ' .
      esc_html((string)($counts['backtest_folds'] ?? 0)) . ' folds · Core execution disabled</div>';
});

add_shortcode('sc_platform_core_predictive_calibration_status', function () {
    $base = rtrim((string) get_option(SCPC_OPTION_BACKEND_URL, ''), '/');
    if (!$base) return '<div class="scpc-status">Platform Core backend URL is not configured.</div>';
    $response = wp_remote_get($base . '/v1/predictive-intelligence/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Probabilistic forecasting status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Probabilistic forecasting status unavailable.</div>';
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Probabilistic Forecasting &amp; Calibration Online</strong><br>' .
      esc_html((string)($counts['probabilistic_forecasts'] ?? 0)) . ' probabilistic forecasts · ' .
      esc_html((string)($counts['calibration_studies'] ?? 0)) . ' calibration studies · ' .
      esc_html((string)($counts['calibration_packages'] ?? 0)) . ' reproducible packages · Core fitting disabled</div>';
});


add_shortcode('sc_platform_core_predictive_ensembles_status', function () {
    $base = rtrim((string) get_option(SCPC_OPTION_BACKEND_URL, ''), '/');
    if (!$base) return '<div class="scpc-status">Platform Core backend URL is not configured.</div>';
    $response = wp_remote_get($base . '/v1/predictive-intelligence/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Predictive ensembles status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Predictive ensembles status unavailable.</div>';
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Predictive Ensembles &amp; Model Comparison Online</strong><br>' .
      esc_html((string)($counts['ensembles'] ?? 0)) . ' ensembles · ' .
      esc_html((string)($counts['ensemble_members'] ?? 0)) . ' members · ' .
      esc_html((string)($counts['comparison_studies'] ?? 0)) . ' comparison studies · ' .
      esc_html((string)($counts['comparison_packages'] ?? 0)) . ' reproducible packages · Core ranking disabled</div>';
});


add_shortcode('sc_platform_core_predictive_monitoring_status', function () {
    $base = rtrim((string) get_option(SCPC_OPTION_BACKEND_URL, ''), '/');
    if (!$base) return '<div class="scpc-status">Platform Core backend URL is not configured.</div>';
    $response = wp_remote_get($base . '/v1/predictive-intelligence/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Predictive monitoring status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Predictive monitoring status unavailable.</div>';
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Anomaly, Change-Point &amp; Early-Warning Intelligence Online</strong><br>' .
      esc_html((string)($counts['monitoring_studies'] ?? 0)) . ' monitoring studies · ' .
      esc_html((string)($counts['anomaly_observations'] ?? 0)) . ' anomaly records · ' .
      esc_html((string)($counts['change_points'] ?? 0)) . ' change points · ' .
      esc_html((string)($counts['early_warning_signals'] ?? 0)) . ' warning signals · Core detection disabled</div>';
});


add_shortcode('sc_platform_core_predictive_spatial_temporal_status', function () {
    $r = wp_remote_get(rtrim(SCPC_CORE_BASE_URL, '/') . '/v1/predictive-intelligence/readiness', array('timeout' => 8));
    if (is_wp_error($r)) return '<span class="scpc-status scpc-status-offline">Spatial-temporal predictive status unavailable.</span>';
    $d = json_decode(wp_remote_retrieve_body($r), true);
    $ok = is_array($d) && !empty($d['spatial_temporal_study_registry_by_core']);
    return $ok ? '<span class="scpc-status scpc-status-online">Spatial-Temporal Predictive Intelligence Online</span>' : '<span class="scpc-status scpc-status-offline">Spatial-Temporal Predictive Intelligence unavailable.</span>';
});


add_shortcode('sc_platform_core_predictive_causal_status', function () {
    $base = rtrim((string) get_option(SCPC_OPTION_BACKEND_URL, ''), '/');
    if (!$base) return '<div class="scpc-status">Platform Core backend URL is not configured.</div>';
    $response = wp_remote_get($base . '/v1/predictive-intelligence/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Causal-predictive status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Causal-predictive status unavailable.</div>';
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Causal-Predictive Integration Online</strong><br>' .
      esc_html((string)($counts['causal_predictive_studies'] ?? 0)) . ' studies · ' .
      esc_html((string)($counts['counterfactual_forecasts'] ?? 0)) . ' counterfactual forecasts · ' .
      esc_html((string)($counts['causal_effect_evidence'] ?? 0)) . ' effect-evidence records · Core causal estimation disabled</div>';
});


add_shortcode('sc_platform_core_predictive_decision_status', function () {
    $base = rtrim((string) get_option(SCPC_OPTION_BACKEND_URL, ''), '/');
    if (!$base) return '<div class="scpc-status">Platform Core backend URL is not configured.</div>';
    $response = wp_remote_get($base . '/v1/predictive-intelligence/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Predictive decision status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Predictive decision status unavailable.</div>';
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Predictive Decision Intelligence Online</strong><br>' .
      esc_html((string)($counts['decision_studies'] ?? 0)) . ' decision studies · ' .
      esc_html((string)($counts['decision_options'] ?? 0)) . ' options · ' .
      esc_html((string)($counts['decision_evidence_bindings'] ?? 0)) . ' evidence bindings · ' .
      esc_html((string)($counts['decision_packages'] ?? 0)) . ' reproducible packages · Core recommendation/optimization disabled</div>';
});


add_shortcode('sc_platform_core_predictive_package_status', function () {
    $response = scpc_core_get('/v1/predictive-intelligence/readiness');
    if (is_wp_error($response)) return '<div class="scpc-status">Reproducible predictive package status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Reproducible predictive package status unavailable.</div>';
    $counts = $data['counts'] ?? array();
    return '<div class="scpc-status"><strong>Reproducible Predictive Intelligence Packages</strong><br />' .
      esc_html((string)($counts['reproducible_predictive_packages'] ?? 0)) . ' packages · ' .
      esc_html((string)($counts['reproducible_predictive_package_components'] ?? 0)) . ' components · ' .
      esc_html((string)($counts['reproducible_predictive_package_verifications'] ?? 0)) . ' verifications · ' .
      esc_html((string)($counts['reproducible_predictive_package_snapshots'] ?? 0)) . ' immutable snapshots · Core execution/reproduction disabled</div>';
});


add_shortcode('sc_platform_core_visual_runtime_status', function () {
    $base = rtrim((string) get_option(SCPC_OPTION_BACKEND_URL, ''), '/');
    if (!$base) return '<div class="scpc-status">Platform Core backend URL is not configured.</div>';
    $response = wp_remote_get($base . '/v1/visual-runtime/readiness', array('timeout' => 10));
    if (is_wp_error($response)) return '<div class="scpc-status">Visual Reasoning Runtime status unavailable.</div>';
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) return '<div class="scpc-status">Visual Reasoning Runtime status unavailable.</div>';
    $counts = isset($data['counts']) && is_array($data['counts']) ? $data['counts'] : array();
    return '<div class="scpc-status"><strong>Visual Reasoning Runtime &amp; Scene Graph Online</strong><br>' .
      esc_html((string)($counts['scenes'] ?? 0)) . ' scenes · ' .
      esc_html((string)($counts['nodes'] ?? 0)) . ' nodes · ' .
      esc_html((string)($counts['edges'] ?? 0)) . ' edges · ' .
      esc_html((string)($counts['snapshots'] ?? 0)) . ' immutable snapshots · renderer execution external to Core</div>';
});


add_shortcode('sc_platform_core_visual_composition_status', function () {
    $base = rtrim(get_option('scpc_core_url', 'https://core.sustainablecatalyst.com'), '/');
    $r = wp_remote_get($base . '/v1/visual-runtime/composition/readiness', array('timeout' => 8));
    if (is_wp_error($r)) return '<div class="scpc-status">Interactive Renderer status unavailable.</div>';
    $d = json_decode(wp_remote_retrieve_body($r), true);
    if (!is_array($d)) return '<div class="scpc-status">Interactive Renderer status unavailable.</div>';
    $n = isset($d['counts']['compositions']) ? intval($d['counts']['compositions']) : 0;
    return '<div class="scpc-status"><strong>Interactive Renderer &amp; View Composition</strong><br>Core ' . esc_html($d['release'] ?? '2.62.0') . ' · ' . esc_html($n) . ' compositions · renderer execution external</div>';
});


add_shortcode('sc_platform_core_visual_grammar_status', function () {
    $d = scpc_get_json('/v1/visual-runtime/grammar/readiness');
    if (!is_array($d)) return '<div class="scpc-status"><strong>Analytical Visualization Grammar</strong><br>Unavailable</div>';
    $n = isset($d['counts']['specifications']) ? intval($d['counts']['specifications']) : 0;
    return '<div class="scpc-status"><strong>Analytical Visualization Grammar</strong><br>Core ' . esc_html($d['release'] ?? '2.63.0') . ' · ' . esc_html($n) . ' specifications · renderer execution external</div>';
});


add_shortcode('sc_platform_core_linked_views_status', function () {
    $d = scpc_get_json('/v1/visual-runtime/linked-views/readiness');
    if (!is_array($d)) return '<div class="scpc-status"><strong>Linked Views &amp; Cross-Filtering</strong><br>Unavailable</div>';
    $c = isset($d['counts']['cross_filters']) ? intval($d['counts']['cross_filters']) : 0;
    $s = isset($d['counts']['selection_sets']) ? intval($d['counts']['selection_sets']) : 0;
    return '<div class="scpc-status"><strong>Linked Views &amp; Cross-Filtering</strong><br>Core ' . esc_html($d['release'] ?? '2.65.0') . ' · ' . esc_html($s) . ' selections · ' . esc_html($c) . ' cross-filters · UI execution external</div>';
});


add_shortcode('sc_platform_core_visual_query_status', function () {
    $data = scpc_request('/v1/visual-runtime/query/readiness');
    if (is_wp_error($data)) return '<div class="scpc-status scpc-status-error">Visual Query &amp; Exploration status unavailable.</div>';
    $release = isset($data['release']) ? esc_html($data['release']) : '2.65.0';
    $sessions = isset($data['counts']['sessions']) ? intval($data['counts']['sessions']) : 0;
    $queries = isset($data['counts']['queries']) ? intval($data['counts']['queries']) : 0;
    $results = isset($data['counts']['results']) ? intval($data['counts']['results']) : 0;
    return '<div class="scpc-status"><strong>Visual Query &amp; Exploration Online</strong><br><span>Core '.$release.' · '.esc_html($sessions).' sessions · '.esc_html($queries).' queries · '.esc_html($results).' external results · Core query execution disabled</span></div>';
});


function scpc_visual_model_construction_status_shortcode() {
    $r = scpc_request('/v1/visual-runtime/model-construction/readiness');
    if (is_wp_error($r)) return '<div class="scpc-status">Visual Model Construction unavailable</div>';
    $d = json_decode(wp_remote_retrieve_body($r), true);
    $c = isset($d['counts']['constructions']) ? intval($d['counts']['constructions']) : 0;
    $m = isset($d['counts']['components']) ? intval($d['counts']['components']) : 0;
    return '<div class="scpc-status"><strong>Visual Model Construction</strong><br>Core ' . esc_html($d['release'] ?? '2.66.0') . ' · ' . esc_html($c) . ' constructions · ' . esc_html($m) . ' components · execution external</div>';
}
add_shortcode('sc_platform_core_visual_model_status', 'scpc_visual_model_construction_status_shortcode');

function scpc_visual_predictive_intelligence_status_shortcode() {
    $r = scpc_request('/v1/visual-runtime/predictive/readiness');
    if (is_wp_error($r)) return '<div class="scpc-status">Visual Predictive Intelligence unavailable</div>';
    $d = json_decode(wp_remote_retrieve_body($r), true);
    $w = isset($d['counts']['workspaces']) ? intval($d['counts']['workspaces']) : 0;
    $f = isset($d['counts']['forecast_overlays']) ? intval($d['counts']['forecast_overlays']) : 0;
    return '<div class="scpc-status"><strong>Visual Predictive Intelligence</strong><br>Core ' . esc_html($d['release'] ?? '2.67.0') . ' · ' . esc_html($w) . ' workspaces · ' . esc_html($f) . ' forecast overlays · predictive execution external</div>';
}
add_shortcode('sc_platform_core_visual_predictive_status', 'scpc_visual_predictive_intelligence_status_shortcode');


// v2.68.0 Visual Forensics Workbench status surface.
add_shortcode('sc_platform_core_visual_forensics_status', function () { return '<div class="sc-core-status"><strong>Visual Forensics Workbench</strong><br>Platform Core 2.68.0 · governed forensic view coordination · analysis/rendering external</div>'; });

// v2.69.0 Visual Decision Intelligence status surface.
add_shortcode('sc_platform_core_visual_decision_status', function () { return '<div class="sc-core-status"><strong>Visual Decision Intelligence</strong><br>Platform Core 2.69.0 · governed decision view coordination · ranking/optimization/execution external</div>'; });

// v2.70.0 Unified Visual Reasoning Engine status surface.
add_shortcode('sc_platform_core_unified_visual_reasoning_status', function () { return '<div class="sc-core-status"><strong>Unified Visual Reasoning Engine</strong><br>Platform Core 2.70.0 · cross-layer semantic orchestration · rendering/computation/inference external</div>'; });


// v2.71.0 Cross-Product Visual Runtime Integration status surface.
add_shortcode('sc_platform_core_cross_product_visual_runtime_status', function () {
    $d = scpc_get_json('/v1/visual-runtime/integrations/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Cross-Product Visual Runtime Integration</strong><br>Unavailable</div>';
    $c = isset($d['counts']['integrations']) ? intval($d['counts']['integrations']) : 0;
    return '<div class="sc-core-status"><strong>Cross-Product Visual Runtime Integration</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.71.0') . ' · ' . esc_html($c) . ' integrations · specialist rendering/computation external</div>';
});


// v2.72.0 Unified Research Project Object Model status surface.
add_shortcode('sc_platform_core_unified_research_project_status', function () {
    $d = scpc_get_json('/v1/research/projects/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Unified Research Project Object Model</strong><br>Unavailable</div>';
    $c = isset($d['counts']['profiles']) ? intval($d['counts']['profiles']) : 0;
    return '<div class="sc-core-status"><strong>Unified Research Project Object Model</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.72.0') . ' · ' . esc_html($c) . ' unified projects · analysis and conclusion generation external</div>';
});


// v2.73.0 Research Lineage & Provenance Graph status surface.
add_shortcode('sc_platform_core_research_lineage_status', function () {
    $d = scpc_get_json('/v1/research/lineage/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Research Lineage &amp; Provenance Graph</strong><br>Unavailable</div>';
    $g = isset($d['counts']['graphs']) ? intval($d['counts']['graphs']) : 0;
    $e = isset($d['counts']['edges']) ? intval($d['counts']['edges']) : 0;
    return '<div class="sc-core-status"><strong>Research Lineage &amp; Provenance Graph</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.73.0') . ' · ' . esc_html($g) . ' graphs · ' . esc_html($e) . ' explicit lineage edges · inference/execution external</div>';
});


// v2.75.0 Methodology & Analysis Run Registry status surface.
function sc_core_methodology_analysis_status() {
    $d = scpc_api_get('/v1/research/methodology/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Methodology &amp; Analysis Run Registry</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Methodology &amp; Analysis Run Registry</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.75.0') . ' · ' . esc_html($c['methodologies'] ?? 0) . ' methods · ' . esc_html($c['runs'] ?? 0) . ' recorded runs · execution/validation external</div>';
}
add_shortcode('sc_core_methodology_analysis_status', 'sc_core_methodology_analysis_status');


// v2.76.0 Research Notebook & Analytical Narrative status surface.
add_shortcode('sc_platform_core_research_notebook_status', function () {
    $d = scpc_get_json('/v1/research/notebooks/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Research Notebook &amp; Analytical Narrative</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Research Notebook &amp; Analytical Narrative</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.76.0') . ' · ' . esc_html($c['notebooks'] ?? 0) . ' notebooks · ' . esc_html($c['entries'] ?? 0) . ' entries · execution/narrative generation external</div>';
});


// v2.77.0 Finding, Claim & Evidence Intelligence status surface.
add_shortcode('sc_platform_core_research_intelligence_status', function () {
    $d = scpc_get_json('/v1/research/intelligence/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Finding, Claim &amp; Evidence Intelligence</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Finding, Claim &amp; Evidence Intelligence</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.77.0') . ' · ' . esc_html($c['findings'] ?? 0) . ' findings · ' . esc_html($c['claims'] ?? 0) . ' claims · ' . esc_html($c['evidence_links'] ?? 0) . ' evidence links · truth/ranking/semantic contradiction resolution external</div>';
});


// v2.78.0 Hypothesis & Competing Explanation Engine status surface.
add_shortcode('sc_platform_core_hypothesis_engine_status', function () {
    $d = scpc_get_json('/v1/research/hypotheses/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Hypothesis &amp; Competing Explanation Engine</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Hypothesis &amp; Competing Explanation Engine</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.78.0') . ' · ' . esc_html($c['hypothesis_sets'] ?? 0) . ' sets · ' . esc_html($c['hypotheses'] ?? 0) . ' hypotheses · ' . esc_html($c['evidence_assessments'] ?? 0) . ' evidence assessments · descriptive comparison only; scoring/ranking/selection external</div>';
});


// v2.79.0 Research Argument & Evidentiary Synthesis Engine status surface.
add_shortcode('sc_platform_core_research_argument_status', function () {
    $d = scpc_get_json('/v1/research/arguments/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Research Argument &amp; Evidentiary Synthesis</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Research Argument &amp; Evidentiary Synthesis</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.79.0') . ' · ' . esc_html($c['arguments'] ?? 0) . ' arguments · ' . esc_html($c['syntheses'] ?? 0) . ' syntheses · ' . esc_html($c['tensions'] ?? 0) . ' evidentiary tensions · generation/scoring/ranking/truth inference external</div>';
});

// v2.80.0 Research Decision Trace & Conclusion Governance status surface.
add_shortcode('sc_platform_core_research_conclusion_status', function () {
    $base = rtrim(get_option('scpc_api_base', 'https://core.sustainablecatalyst.com'), '/');
    $r = wp_remote_get($base . '/v1/research/conclusions/readiness', array('timeout' => 10));
    if (is_wp_error($r)) return '<div class="sc-core-status"><strong>Research Conclusion Governance</strong><br>Core endpoint unavailable.</div>';
    $d = json_decode(wp_remote_retrieve_body($r), true); $c = is_array($d) ? ($d['counts'] ?? array()) : array();
    return '<div class="sc-core-status"><strong>Research Decision Trace &amp; Conclusion Governance</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.80.0') . ' · ' . esc_html($c['conclusions'] ?? 0) . ' conclusions · ' . esc_html($c['caveats'] ?? 0) . ' caveats · ' . esc_html($c['dissent_records'] ?? 0) . ' dissent records · researcher-directed conclusions</div>';
});


// v2.81.0 Reproducible Research Publication & Scholarly Output Engine status surface.
add_shortcode('sc_platform_core_research_publication_status', function () {
    $d = scpc_get_json('/v1/research/publications/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Research Publication &amp; Scholarly Output</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Reproducible Research Publication &amp; Scholarly Output</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.81.0') . ' · ' . esc_html($c['publications'] ?? 0) . ' publications · ' . esc_html($c['sections'] ?? 0) . ' sections · ' . esc_html($c['citations'] ?? 0) . ' citations · structural readiness and provenance; authorship/quality judgment/external publication remain researcher-directed</div>';
});


// v2.82.0 Peer Review, Replication & Rebuttal Intelligence status surface.
add_shortcode('sc_platform_core_peer_review_status', function () {
    $d = scpc_get_json('/v1/research/peer-review/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Peer Review, Replication &amp; Rebuttal Intelligence</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Peer Review, Replication &amp; Rebuttal Intelligence</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.82.0') . ' · ' . esc_html($c['reviews'] ?? 0) . ' reviews · ' . esc_html($c['replication_studies'] ?? 0) . ' replication studies · ' . esc_html($c['rebuttals'] ?? 0) . ' rebuttals · descriptive provenance only; quality scoring, replication inference, and publication decisions remain human-directed</div>';
});


// v2.83.0 Cross-Study Evidence Synthesis & Meta-Research status surface.
add_shortcode('sc_platform_core_evidence_synthesis_status', function () {
    $d = scpc_get_json('/v1/research/evidence-synthesis/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Cross-Study Evidence Synthesis &amp; Meta-Research</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Cross-Study Evidence Synthesis &amp; Meta-Research</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.83.0') . ' · ' . esc_html($c['syntheses'] ?? 0) . ' syntheses · ' . esc_html($c['studies'] ?? 0) . ' studies · ' . esc_html($c['meta_analyses'] ?? 0) . ' external meta-analysis records · provenance-aware synthesis; literature search, inclusion decisions, effect computation, pooling, scoring, and truth inference remain external/researcher-directed</div>';
});


// v2.84.0 Research Program & Longitudinal Knowledge Graph status surface.
add_shortcode('sc_platform_core_research_program_status', function () {
    $d = scpc_get_json('/v1/research/programs/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Research Program &amp; Longitudinal Knowledge Graph</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Research Program &amp; Longitudinal Knowledge Graph</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.84.0') . ' · ' . esc_html($c['programs'] ?? 0) . ' programs · ' . esc_html($c['longitudinal_nodes'] ?? 0) . ' graph nodes · ' . esc_html($c['knowledge_states'] ?? 0) . ' knowledge states · descriptive longitudinal governance; priority ranking, auto-linking, funding allocation, forecasting, causal/truth inference remain researcher-directed</div>';
});


// v2.85.0 Research Portfolio & Institutional Knowledge Governance status surface.
add_shortcode('sc_platform_core_research_portfolio_status', function () {
    $d = scpc_get_json('/v1/research/portfolios/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Research Portfolio &amp; Institutional Knowledge Governance</strong><br>Unavailable</div>';
    $c = $d['counts'] ?? array();
    return '<div class="sc-core-status"><strong>Research Portfolio &amp; Institutional Knowledge Governance</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.85.0') . ' · ' . esc_html($c['portfolios'] ?? 0) . ' portfolios · ' . esc_html($c['program_memberships'] ?? 0) . ' program memberships · ' . esc_html($c['risks'] ?? 0) . ' risks · descriptive institutional governance; ranking, prioritization, resource allocation, optimization, governance decisions, forecasting, and truth inference remain human-directed</div>';
});


// v2.86.0 Scientific Study & Investigation Protocol Model status surface.
add_shortcode('sc_platform_core_research_protocol_status', function () {
    $d = scpc_get_json('/v1/research/protocols/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Scientific Study &amp; Investigation Protocol Model</strong><br>Unavailable</div>';
    $c = $d['counts'] ?? array();
    return '<div class="sc-core-status"><strong>Scientific Study &amp; Investigation Protocol Model</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.86.0') . ' · ' . esc_html($c['protocols'] ?? 0) . ' protocols · ' . esc_html($c['method_plans'] ?? 0) . ' method plans · ' . esc_html($c['deviations'] ?? 0) . ' deviations · protocol registry and provenance only; execution, data collection, analysis, ethics certification, and truth inference remain external/human-directed</div>';
});

// v2.87.0 Computation, Analysis & Execution Lineage status surface.
add_shortcode('sc_platform_core_computation_lineage_status', function () {
    $d = scpc_get_json('/v1/research/computation-lineage/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Computation, Analysis &amp; Execution Lineage</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Computation, Analysis &amp; Execution Lineage</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.87.0') . ' · ' . esc_html($c['executions'] ?? 0) . ' executions · ' . esc_html($c['inputs'] ?? 0) . ' inputs · ' . esc_html($c['outputs'] ?? 0) . ' outputs · provenance/lineage registry only; Python/R/Julia/ML/Workbench execution and result inference remain external</div>';
});


// v2.88.0 Unified Findings, Claims & Inference Engine status surface.
add_shortcode('sc_platform_core_unified_inference_status', function () {
    $d = scpc_get_json('/v1/research/inferences/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Unified Findings, Claims &amp; Inference Engine</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Unified Findings, Claims &amp; Inference Engine</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.88.0') . ' · ' . esc_html($c['inferences'] ?? 0) . ' inferences · ' . esc_html($c['classifications'] ?? 0) . ' classifications · ' . esc_html($c['basis_bindings'] ?? 0) . ' basis bindings · explicit epistemic semantics; inference generation, causal determination, scoring, validation, ranking, contradiction resolution, and truth determination remain external/researcher-directed</div>';
});


// v2.89.0 Research Quality, Bias & Methodological Audit Engine status surface.
add_shortcode('sc_platform_core_research_quality_audit_status', function () {
    $d = scpc_get_json('/v1/research/quality-audits/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Research Quality, Bias &amp; Methodological Audit Engine</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Research Quality, Bias &amp; Methodological Audit Engine</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.89.0') . ' · ' . esc_html($c['audits'] ?? 0) . ' audits · ' . esc_html($c['checks'] ?? 0) . ' checks · ' . esc_html($c['findings'] ?? 0) . ' audit findings · descriptive/declared methodological audit evidence only; bias inference, quality scoring, ranking, validity certification, and truth determination remain external/human-directed</div>';
});


// v2.90.0 Research Workflow & Orchestration Engine status.
add_shortcode('sc_platform_core_research_workflow_status', function () {
    $url = rtrim(SCPC_API_BASE, '/') . '/v1/research/workflows/readiness';
    $r = wp_remote_get($url, array('timeout' => 8));
    if (is_wp_error($r)) return '<div class="sc-core-status">Research Workflow Engine unavailable.</div>';
    $d = json_decode(wp_remote_retrieve_body($r), true);
    if (!is_array($d)) return '<div class="sc-core-status">Research Workflow Engine unavailable.</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Research Workflow &amp; Orchestration Engine</strong><br>Workflows: '.intval($c['workflows'] ?? 0).' · Stages: '.intval($c['stages'] ?? 0).' · Handoffs: '.intval($c['handoffs'] ?? 0).'</div>';
});


// v2.91.0 Cross-Product Research Context & Handoff Protocol status.
add_shortcode('sc_platform_core_research_context_handoff_status', function () {
    $url = rtrim(SCPC_API_BASE, '/') . '/v1/research/context-handoffs/readiness';
    $r = wp_remote_get($url, array('timeout' => 8));
    if (is_wp_error($r)) return '<div class="sc-core-status">Research Context Handoff unavailable.</div>';
    $d = json_decode(wp_remote_retrieve_body($r), true);
    if (!is_array($d)) return '<div class="sc-core-status">Research Context Handoff unavailable.</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Cross-Product Research Context &amp; Handoff</strong><br>Contexts: '.intval($c['contexts'] ?? 0).' · Packages: '.intval($c['packages'] ?? 0).' · Acknowledgements: '.intval($c['acknowledgements'] ?? 0).'</div>';
});

// v2.92.0 Research Project State, Versioning & Reproducibility status.
add_shortcode('sc_platform_core_research_project_state_status', function () {
    $url = rtrim(SCPC_API_BASE, '/') . '/v1/research/project-state/readiness';
    $r = wp_remote_get($url, array('timeout' => 8));
    if (is_wp_error($r)) return '<div class="sc-core-status">Research Project State unavailable.</div>';
    $d = json_decode(wp_remote_retrieve_body($r), true);
    if (!is_array($d)) return '<div class="sc-core-status">Research Project State unavailable.</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Research Project State, Versioning &amp; Reproducibility</strong><br>States: '.intval($c['states'] ?? 0).' · Versions: '.intval($c['versions'] ?? 0).' · Reconstruction Plans: '.intval($c['reconstruction_plans'] ?? 0).'</div>';
});


// v2.93.0 Research Roles, Agents & Contributor Provenance Framework status.
add_shortcode('sc_platform_core_research_contributor_provenance_status', function () {
    $url = rtrim(SCPC_API_BASE, '/') . '/v1/research/contributors/readiness';
    $r = wp_remote_get($url, array('timeout' => 8));
    if (is_wp_error($r)) return '<div class="sc-core-status">Research Contributor Provenance unavailable.</div>';
    $d = json_decode(wp_remote_retrieve_body($r), true);
    if (!is_array($d)) return '<div class="sc-core-status">Research Contributor Provenance unavailable.</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Research Roles, Agents &amp; Contributor Provenance</strong><br>Contributors: '.intval($c['contributors'] ?? 0).' · Contributions: '.intval($c['contributions'] ?? 0).' · Agent Actions: '.intval($c['agent_actions'] ?? 0).'</div>';
});


// v2.94.0 Research Validation & Challenge Engine status.
function sc_platform_core_research_validation_challenge_status_shortcode() {
  return '<div class="sc-platform-core-status" data-core-feature="research-validation-challenge">Research Validation &amp; Challenge Engine · Core v2.94.0</div>';
}
add_shortcode('sc_platform_core_research_validation_challenge_status', 'sc_platform_core_research_validation_challenge_status_shortcode');


// v2.95.0 Scholarly Interoperability & Research Packaging status.
add_shortcode('sc_platform_core_scholarly_interoperability_status', function () {
    $d = scpc_get_json('/v1/research/scholarly-packages/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Scholarly Interoperability &amp; Research Packaging</strong><br>Unavailable</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Scholarly Interoperability &amp; Research Packaging</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.95.0') . ' · ' . esc_html($c['packages'] ?? 0) . ' packages · ' . esc_html($c['citations'] ?? 0) . ' citations · ' . esc_html($c['identifiers'] ?? 0) . ' identifiers · interoperability metadata and packaging only; identifier registration, publishing, notebook execution, scientific validation, and reproducibility certification remain external</div>';
});


// v2.96.0 Unified Research Runtime Contract status.
function sc_platform_core_unified_research_runtime_status() {
    $d = scpc_core_json('/v1/research/runtime-contract/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Unified Research Runtime Contract</strong><br>Runtime status unavailable.</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Unified Research Runtime Contract</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.96.0') . ' · ' . esc_html($c['contracts'] ?? 0) . ' contracts · ' . esc_html($c['product_bindings'] ?? 0) . ' product bindings · ' . esc_html($c['exchanges'] ?? 0) . ' exchanges · standardized declared runtime interfaces; specialist execution, authorization, scientific validation, and autonomous routing remain external</div>';
}
add_shortcode('sc_platform_core_unified_research_runtime_status', 'sc_platform_core_unified_research_runtime_status');


// v2.97.0 Platform Research Integration Certification status.
function sc_platform_core_research_integration_certification_status() {
    $d = scpc_core_json('/v1/research/integration-certification/readiness');
    if (!is_array($d)) return '<div class="sc-core-status"><strong>Platform Research Integration Certification</strong><br>Certification status unavailable.</div>';
    $c = isset($d['counts']) && is_array($d['counts']) ? $d['counts'] : array();
    return '<div class="sc-core-status"><strong>Platform Research Integration Certification</strong><br>Platform Core ' . esc_html($d['release'] ?? '2.97.0') . ' · ' . esc_html($c['suites'] ?? 0) . ' suites · ' . esc_html($c['runs'] ?? 0) . ' runs · ' . esc_html($c['case_results'] ?? 0) . ' case results · runtime-contract conformance evidence only; scientific validity, product quality, authorization, ranking, and truth remain outside Core</div>';
}
add_shortcode('sc_platform_core_research_integration_certification_status', 'sc_platform_core_research_integration_certification_status');

function scpc_analytical_result_status_shortcode() {
    $ready = scpc_api_get('/v1/analytics/results/readiness');
    if (is_wp_error($ready)) {
        return '<div class="scpc-card scpc-error"><strong>Analytical result provenance unavailable</strong><p>' . esc_html($ready->get_error_message()) . '</p></div>';
    }
    $version = isset($ready['catalyst_analytics_r_version']) ? sanitize_text_field($ready['catalyst_analytics_r_version']) : 'unknown';
    $counts = isset($ready['counts']) && is_array($ready['counts']) ? $ready['counts'] : [];
    $results = isset($counts['results']) ? intval($counts['results']) : 0;
    $snapshots = isset($counts['snapshots']) ? intval($counts['snapshots']) : 0;
    ob_start(); ?>
    <section class="scpc-card">
        <p class="scpc-kicker">Analytical Result &amp; Provenance Integration</p>
        <h3>Platform Core v3.3 analytical evidence layer</h3>
        <p><strong>Status:</strong> Online · <strong>Catalyst Analytics R:</strong> <?php echo esc_html($version); ?> · <strong>Results:</strong> <?php echo esc_html(number_format_i18n($results)); ?> · <strong>Snapshots:</strong> <?php echo esc_html(number_format_i18n($snapshots)); 
require_once __DIR__ . '/includes/class-sc-core-investigation-workspace.php';
?></p>
        <p class="scpc-meta">Core records analytical results, provenance, uncertainty, diagnostics, and reproducibility references. Computation remains in governed specialist runtimes such as Workspace.</p>
    </section>
    <?php return ob_get_clean();
}
add_shortcode('sc_platform_core_analytical_result_status', 'scpc_analytical_result_status_shortcode');



// v3.3.0 Statistical Reasoning Object Model status.
function scpc_statistical_reasoning_status_shortcode() {
    $ready = scpc_api_get('/v1/analytics/statistical-reasoning/readiness');
    if (is_wp_error($ready)) return '<div class="scpc-card scpc-error"><strong>Statistical reasoning unavailable</strong><p>' . esc_html($ready->get_error_message()) . '</p></div>';
    $counts = isset($ready['counts']) && is_array($ready['counts']) ? $ready['counts'] : array();
    $provider = sanitize_text_field($ready['catalyst_analytics_r_version'] ?? 'unknown');
    return '<section class="scpc-card"><p class="scpc-kicker">Statistical Reasoning Object Model</p><h3>Platform Core v3.3 statistical evidence layer</h3><p><strong>Status:</strong> Online · <strong>Catalyst Analytics R:</strong> ' . esc_html($provider) . ' · <strong>Reasoning objects:</strong> ' . intval($counts['reasoning_objects'] ?? 0) . ' · <strong>Diagnostics:</strong> ' . intval($counts['diagnostics'] ?? 0) . ' · <strong>Interpretations:</strong> ' . intval($counts['interpretations'] ?? 0) . '</p><p class="scpc-meta">Diagnostics, assumptions, robustness evidence, comparisons, coefficients, and intervals are recorded as evidence. Core does not certify validity, infer statistical significance, select a preferred model, or replace human interpretation.</p></section>';
}
add_shortcode('sc_platform_core_statistical_reasoning_status', 'scpc_statistical_reasoning_status_shortcode');


// v3.21.0 Uncertainty & Probabilistic Evidence Integration status.
function sc_platform_core_uncertainty_probabilistic_status() {
    $ready = scpc_api_get('/v1/analytics/uncertainty-evidence/readiness');
    if (is_wp_error($ready)) return '<div class="scpc-card scpc-error"><strong>Uncertainty evidence unavailable</strong></div>';
    $c = isset($ready['counts']) && is_array($ready['counts']) ? $ready['counts'] : array();
    return '<section class="scpc-card"><p class="scpc-kicker">Uncertainty &amp; Probabilistic Evidence</p><h3>Platform Core v3.21 governed uncertainty layer</h3><p><strong>Status:</strong> Online · <strong>Studies:</strong> '.intval($c['studies'] ?? 0).' · <strong>Sensitivity indices:</strong> '.intval($c['sensitivity_indices'] ?? 0).' · <strong>Snapshots:</strong> '.intval($c['snapshots'] ?? 0).'</p><p class="scpc-meta">Monte Carlo, Latin hypercube, Morris, and Sobol outputs are preserved as governed evidence. Core does not execute uncertainty analysis, infer causality, rank parameters, select policy, or certify scientific validity.</p></section>';
}
add_shortcode('sc_platform_core_uncertainty_probabilistic_status', 'sc_platform_core_uncertainty_probabilistic_status');
