### SecurityScheme

```python
SecurityScheme = Annotated[
    Union[
        HttpSecurityScheme,
        ApiKeySecurityScheme,
        OAuth2SecurityScheme,
        OpenIdConnectSecurityScheme,
    ],
    Field(discriminator="type"),
]

```

A security scheme for authentication.
