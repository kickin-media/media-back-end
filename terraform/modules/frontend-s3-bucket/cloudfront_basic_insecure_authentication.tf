resource "aws_cloudfront_function" "insecure_basic_auth" {
  name    = "basic-auth-viewer-request-${var.frontend_bucket_name}"
  runtime = "cloudfront-js-2.0"
  comment = "Simple Basic Auth for entire site"
  publish = true

  code = <<-EOF
function handler(event) {
  var req = event.request;
  var headers = req.headers;

  var expected = 'Basic ${base64encode("${var.frontend_insecure_auth_user}:${var.frontend_insecure_auth_password}")}';

  if (headers.authorization && headers.authorization.value === expected) {
    return req; // let it through
  }

  return {
    statusCode: 401,
    statusDescription: 'Unauthorized',
    headers: {
      'www-authenticate': { value: 'Basic realm="${var.frontend_insecure_auth_prompt}"' },
      'cache-control': { value: 'no-store, no-cache, must-revalidate' },
      'pragma': { value: 'no-cache' }
    },
    body: 'Access Denied. Refresh the page to try again. ${var.frontend_insecure_auth_prompt}'
  };
}
EOF
}

resource "aws_cloudfront_function" "noop" {
  name    = "noop-viewer-request-${var.frontend_bucket_name}"
  runtime = "cloudfront-js-2.0"
  comment = "No-op: returns the request unchanged"
  publish = true

  code = <<-EOF
function handler(event) {
  return event.request;
}
EOF
}

resource "aws_cloudfront_cache_policy" "vary_on_auth" {
  name    = "vary-on-authorization-${var.frontend_bucket_name}"
  comment = "Vary cache by Authorization to avoid mixing authed/unauth responses"

  default_ttl = 3600
  max_ttl     = 86400
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true

    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Authorization"]
      }
    }

    query_strings_config {
      query_string_behavior = "none"
    }
  }
}

resource "aws_cloudfront_origin_request_policy" "no_auth" {
  name    = "no-authorization-to-origin-${var.frontend_bucket_name}"
  comment = "Do not forward Authorization header to S3"

  headers_config {
    header_behavior = "none"
  }

  cookies_config {
    cookie_behavior = "none"
  }

  query_strings_config {
    query_string_behavior = "none"
  }
}
