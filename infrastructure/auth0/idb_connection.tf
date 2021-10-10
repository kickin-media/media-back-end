resource "auth0_connection" "idb_connection" {
  name     = "kick-in-idb"
  strategy = "oauth2"
  options {
    client_id              = "kick-in-media"
    client_secret          = var.idb_connection_client_secret
    scopes                 = ["all"]
    authorization_endpoint = "https://oauth.kick-in.nl/authorize"
    token_endpoint         = "https://oauth.kick-in.nl/token"

    scripts = {
      fetchUserProfile = <<EOF
function fetchUserProfile(accessToken, context, callback) {
  request.get(
    {
      url: 'https://idb.kick-in.nl/apiv3/authenticated/personinfo',
      headers: {
        'Authorization': 'Bearer ' + accessToken,
      }
    },
    (err, resp, body) => {
      if (err) {
        return callback(err);
      }

      if (resp.statusCode !== 200) {
        return callback(new Error(body));
      }

      let bodyParsed;
      try {
        bodyParsed = JSON.parse(body);
      } catch (jsonError) {
        return callback(new Error(body));
      }

      const profile = {
        user_id: bodyParsed.person.id,
        given_name: bodyParsed.person.firstname,
        nickname: bodyParsed.person.firstname,
        name: bodyParsed.person.fullname,
        email_verified: true,
        email: bodyParsed.person.email
      };

      callback(null, profile);
    }
  );
}
EOF
    }
  }
}