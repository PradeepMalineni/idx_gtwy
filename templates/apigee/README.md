# Apigee Proxy Seed Template

This directory contains the seed template for generating Apigee API proxy bundles.

## Structure

```
apiproxy/
├── {api-name}.xml          # Main proxy configuration
├── proxies/
│   └── default.xml         # Proxy endpoint
├── targets/
│   └── default.xml         # Target endpoint
├── policies/
│   ├── Spike-Arrest.xml    # Rate limiting
│   ├── Verify-API-Key.xml  # API key verification
│   ├── CORS.xml            # CORS headers
│   └── Response-Cache.xml  # Response caching
└── resources/
    └── jsc/                # JavaScript resources
```

## Policies Included

1. **Spike Arrest** - Rate limiting (100 requests/minute)
2. **Verify API Key** - API key authentication
3. **CORS** - Cross-origin resource sharing
4. **Response Cache** - Cache responses for 5 minutes

## Customization

The generator will:
- Replace API name placeholders
- Set base path from OpenAPI spec
- Configure target URL
- Add additional policies as needed

## Usage

This template is used automatically by the `proxy_generator` module.
You can customize files here to change the default proxy structure.

