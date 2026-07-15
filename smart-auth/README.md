# OAuth2 and SMART on FHIR demonstration

This lab places an OAuth2/OIDC gateway in front of the HAPI FHIR endpoint. Keycloak provides authorization-code with PKCE for a public SMART demo client and client credentials for the synthetic Mirth backend. OAuth2 Proxy verifies tokens before forwarding requests.

- Keycloak: `http://10.20.1.157:8180`
- Protected FHIR gateway: `http://10.20.1.157:8091/fhir`
- SMART discovery: `http://10.20.1.157:8091/.well-known/smart-configuration`

This is a homelab demonstration over HTTP. Production use requires TLS, externally managed secrets, hardened Keycloak settings, restricted network routes, authorization policy enforcement for individual SMART scopes, audit review and a supported HA design.

The public `smart-demo-client` exercises authorization code plus PKCE. The `mirth-service` client demonstrates machine-to-machine OAuth with `system/*.read` and `system/*.write` scope labels. It uses a symmetric client secret for the lab; the full SMART Backend Services profile uses asymmetric client authentication and should be the next hardening step.
