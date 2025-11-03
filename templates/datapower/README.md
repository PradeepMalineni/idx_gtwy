# DataPower Configuration Seed Template

This directory contains the seed template for generating DataPower configurations.

## Structure

```
datapower/
├── {api-name}-mpgw.xml     # Multi-Protocol Gateway configuration
├── {api-name}-policy.xml   # Processing policy
└── {api-name}-api.yaml     # API gateway configuration
```

## Components

### Multi-Protocol Gateway (MPGW)
- HTTP/HTTPS frontend handler
- Backend routing configuration
- Protocol settings

### Processing Policy
- Request/response filters
- Rate limiting
- OAuth verification
- Backend routing rules

### API Configuration
- API metadata
- Security policies (OAuth, mTLS, PCI protection)
- Backend configuration
- Path mappings

## Security Features

1. **OAuth 2.0** - Token validation
2. **mTLS** - Mutual TLS authentication  
3. **PCI Protection** - Card number masking and encryption
4. **Rate Limiting** - Protect backend services

## Usage

This template is used automatically by the `proxy_generator` module.
Customize files here to change default DataPower configuration.

