package com.bauerfinanz.gutachten.authorizer.integration;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.containsString;
import static org.hamcrest.MatcherAssert.assertThat;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.junit.jupiter.api.TestInstance.Lifecycle;

import com.amazonaws.services.lambda.runtime.events.APIGatewayCustomAuthorizerEvent;
import com.fasterxml.jackson.core.JsonProcessingException;

import io.quarkus.test.junit.QuarkusTest;

/**
 * The Class TokenAuthorizerIntegrationTest.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@QuarkusTest
@TestInstance(Lifecycle.PER_CLASS)
class TokenAuthorizerIntegrationTest {

  @Test
  void emptyEventTest() {

    final String response = given().contentType("application/json").accept("application/json").when().post().then()
      .statusCode(500).extract().asString();

    assertThat(response, containsString("No content to map due to end-of-input"));
    assertThat(response, containsString("MismatchedInputException"));
  }

  @Test
  void emptyTokenTest() {
    final String response = given().contentType("application/json").accept("application/json")
      .body(APIGatewayCustomAuthorizerEvent.builder().build()).when().post().then()
      .statusCode(500).extract().asString();

    assertThat(response, containsString("No authorizer token available"));
    assertThat(response, containsString("RuntimeException"));
  }

  @Test
  void verifyExpiredTest() throws JsonProcessingException {
    final APIGatewayCustomAuthorizerEvent event = APIGatewayCustomAuthorizerEvent.builder()
      .withQueryStringParameters(Map.of("token",
        "eyJraWQiOiJpZmJSWm5WSW1lZWZcL2lEVGl4Z3QwbHpEck5Vb1NBUEZpbXlXdE9tRkRwND0iLCJhbGciOiJSUzI1NiJ9.eyJhdF9oYXNoIjoiVkFvaTNnNWNieVFMMGxvWi0wNkZ5QSIsInN1YiI6IjYwNzljNTBmLTY4OWMtNDkwZS05ZTUyLTY5NWE2MTUxMGJkNCIsImNvZ25pdG86Z3JvdXBzIjpbImV1LXdlc3QtMV9Jd01hQk1FUlpfY2VudHJhbERQUEF1dGgiXSwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9Jd01hQk1FUloiLCJjb2duaXRvOnVzZXJuYW1lIjoiY2VudHJhbGRwcGF1dGhfYmM2NGNiODEtZDAzYS00MDA4LTg2OGUtYjhkNjY1ZWNjNjMwIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWZhYW5xNCIsImdpdmVuX25hbWUiOiJNYXJrdXMiLCJub25jZSI6Ijhuek1wc0stdkROT1NURlc4eWlrdVhyNmRRaWo1NmVZUHRmaXJsVW15SEhmVGVvVm80NVMxMG9tcDdsWE1HMFd3UUVtTFVBWmhpVDZnQmIxci10ODBEV0ZmMW5rbHRYN1hlWjh4cUdYYmRUQjNkcG45OW9QcnRMREZoY0taSUR3N3lJQVpDaEpHX3hlRS1pYUE2emY2LTk1aXhWdUVKUG9TeG95S2k2Wi1HZyIsImF1ZCI6IjU2ZjFocHV1Z2JvZ3BmbzQ3YmVsdnVjOGxmIiwiaWRlbnRpdGllcyI6W3sidXNlcklkIjoiYmM2NGNiODEtZDAzYS00MDA4LTg2OGUtYjhkNjY1ZWNjNjMwIiwicHJvdmlkZXJOYW1lIjoiY2VudHJhbERQUEF1dGgiLCJwcm92aWRlclR5cGUiOiJPSURDIiwiaXNzdWVyIjpudWxsLCJwcmltYXJ5IjoidHJ1ZSIsImRhdGVDcmVhdGVkIjoiMTYyMDIyNjEzMzM1OSJ9XSwidG9rZW5fdXNlIjoiaWQiLCJzY29wZSI6IlAxIFAyIFAzIFA0IFA1IFAxMCIsImF1dGhfdGltZSI6MTYyMjY0NjQ0NSwiZXhwIjoxNjIyNjUwMDQ1LCJpYXQiOjE2MjI2NDY0NDYsImZhbWlseV9uYW1lIjoiUGljaGxlciIsImVtYWlsIjoiZXh0ZXJuLm1hcmt1cy5waWNobGVyQHBvcnNjaGUuZGUifQ.PlwkgGHlARrJPBps7a9rgRE-m7ca7Wy823ACUkMk4gMurVZLr3nlTAo3i-nhKTUyLpWbNNgNDFz8DaDUy_RBVWNQgS79cmlHd2jPS4aLPKGoyLb4N_h3dcKjX6ipIkRxvXhcT-yvTVO5__C2Irs3d7BpLcD8-YwSsXemjAmNLHdMgPAiC2fyu88dE5JbRt7ePsW-hDWuWjswevy8pyWHrdg5pXCm-rScqS5z7rMsoyjfOFuc_varOvkVRT5O-tA2MPpbOdz6oebovjgaUjLZ122RnXJn2dXpAhJXdd7OmsBR8wT6ITZT_INCdwxbo0GEBUCqs8Vz-BjrmwWZOCp3JA"))
      .withMethodArn("arn:aws:execute-api:eu-west-1:287495171296:e4pm8bqgv0/icos/$connect")
      .withType("REQUEST")
      .build();

    final String response = given().contentType("application/json").accept("application/json").body(event)
      .when().post().then().statusCode(500).extract().asString();

    assertThat(response, containsString("Authorization token is expired"));
    assertThat(response, containsString("RuntimeException"));

  }

}
