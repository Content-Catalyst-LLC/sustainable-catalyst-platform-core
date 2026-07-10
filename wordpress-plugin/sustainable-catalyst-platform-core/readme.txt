=== Sustainable Catalyst Platform Core ===
Contributors: content-catalyst
Tags: knowledge graph, entity registry, provenance, sustainable catalyst
Requires at least: 6.4
Tested up to: 6.8
Requires PHP: 8.0
Stable tag: 2.5.0
License: MIT

WordPress status and entity lookup client for Sustainable Catalyst Platform Core.

== Installation ==

1. Upload and activate the plugin.
2. Go to Settings → Platform Core.
3. Enter the Platform Core backend URL.
4. Use [sc_platform_core_status].
5. Use [sc_platform_core_entity id="sc:product:workbench"].

The plugin never exposes the Platform Core write key in frontend code.

== 2.1.0 ==

* Adds reviewed relationship neighborhood shortcode.
* Adds Knowledge Explorer launch shortcode.
* Supports Platform Core v2.1.0 graph APIs and JSON-LD records.


== 2.2.0 ==

* Adds Evidence Ledger integrity and statistics shortcode.
* Adds claim evidence manifest shortcode.
* Adds Evidence Explorer launch shortcode.
* Supports claims, source snapshots, provenance activities, calculation traces, reviews, and ledger verification.


== 2.3.0 ==

* Adds Developer Portal launch shortcode.
* Adds public API plan cards.
* Supports the Unified Public API, scoped credentials, usage controls, SDK assets, and signed webhooks.

== 2.4.0 ==

* Adds Trust Center launch and public trust-status shortcodes.
* Supports evaluation definitions, runs, check results, findings, incidents, limitations, attestations, and machine-readable trust status.

== 2.5.0 ==

* Adds Signature Dossier Center launch shortcode.
* Adds public signature dossier verification cards.
* Adds end-to-end workflow status cards.
* Supports Platform Core v2.5.0 workflow and dossier APIs.
