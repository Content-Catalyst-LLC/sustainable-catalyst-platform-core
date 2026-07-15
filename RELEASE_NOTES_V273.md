# Sustainable Catalyst Platform Core v2.7.3

## Economics and Official Statistics Connector Pack

This release adds a normalized economics record layer and twelve new governed free-source connectors: IMF, OECD, Eurostat, ECB, BIS, BEA, BLS, Census, SEC EDGAR, EIA, FAOSTAT, and ILOSTAT. Existing World Bank, FRED, and UN Comtrade integrations remain available.

### Safety and licensing

- No paid API subscriptions or credit-card-required providers.
- IMF, BEA, and EIA fail closed until free registration configuration is supplied.
- SEC uses bounded fair-access requests with an identifying User-Agent.
- Source, license, attribution, release frequency, content hash, and raw provenance are retained.
- Credential-bearing query values are redacted from persisted parameters and normalized source URLs.
- The release does not represent periodic official statistics as real-time market data.

### Database and APIs

Migration `0010` creates `economic_data_records`. Internal routes use `/v1/economics`; public routes use `/api/v1/economics` with `data:read`.
