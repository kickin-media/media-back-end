resource "auth0_client" "frontend_application" {
  name                                = "Kick-In Media Tool"
  app_type                            = "spa"
  is_first_party                      = true
  oidc_conformant                     = true
  callbacks                           = []
  allowed_origins                     = []
  grant_types                         = ["authorization_code", "implicit", "refresh_token"]
  allowed_logout_urls                 = []
  web_origins                         = []
  jwt_configuration {
    lifetime_in_seconds = 3600
    secret_encoded      = false
    alg                 = "RS256"
  }
  refresh_token {
    rotation_type                = "rotating"
    expiration_type              = "expiring"
    token_lifetime               = 84600
    infinite_token_lifetime      = false
    idle_token_lifetime          = 3600
  }
}