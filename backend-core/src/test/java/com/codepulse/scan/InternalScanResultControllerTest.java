package com.codepulse.scan;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.security.oauth2.client.OAuth2ClientAutoConfiguration;
import org.springframework.boot.autoconfigure.security.oauth2.client.servlet.OAuth2ClientWebSecurityAutoConfiguration;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import com.codepulse.auth.service.JwtService;
import com.codepulse.scan.dto.ScanDetailResponse;
import com.codepulse.scan.dto.ScanResultCallbackRequest;
import com.fasterxml.jackson.databind.ObjectMapper;

@WebMvcTest(
        controllers = InternalScanResultController.class,
        excludeAutoConfiguration = {
                OAuth2ClientAutoConfiguration.class,
                OAuth2ClientWebSecurityAutoConfiguration.class
        })
@AutoConfigureMockMvc(addFilters = false)
@TestPropertySource(properties = "fastapi.internal-api-key=test-key")
class InternalScanResultControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ScanService scanService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserDetailsService userDetailsService;

    @Test
    void receiveScanResultsAcceptsValidInternalApiKey() throws Exception {
        UUID scanId = UUID.randomUUID();
        UUID repositoryId = UUID.randomUUID();
        when(scanService.applyScanResults(eq(scanId), any(ScanResultCallbackRequest.class)))
                .thenReturn(scanDetail(scanId, repositoryId, "COMPLETED"));

        mockMvc.perform(post("/internal/scans/{scanId}/results", scanId)
                .with(csrf())
                .header("Authorization", "Bearer test-key")
                .contentType("application/json")
                .content("""
                        {
                          "status": "COMPLETED",
                          "scores": {
                            "qualityScore": 95,
                            "securityScore": 90,
                            "maintainabilityScore": 88
                          },
                          "metadata": {"totalFindings": 0},
                          "findings": []
                        }
                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(scanId.toString()))
                .andExpect(jsonPath("$.status").value("COMPLETED"));
    }

    @Test
    void receiveScanResultsRejectsInvalidInternalApiKey() throws Exception {
        mockMvc.perform(post("/internal/scans/{scanId}/results", UUID.randomUUID())
                .with(csrf())
                .header("Authorization", "Bearer wrong")
                .contentType("application/json")
                .content(objectMapper.writeValueAsString(new ScanResultCallbackRequest(
                        com.codepulse.scan.domain.ScanStatus.RUNNING,
                        null,
                        null,
                        null,
                        null))))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("UNAUTHORIZED"));
    }

    private ScanDetailResponse scanDetail(UUID scanId, UUID repositoryId, String status) {
        return new ScanDetailResponse(
                scanId,
                repositoryId,
                "https://github.com/codepulse/backend-core",
                "codepulse/backend-core",
                status,
                95,
                90,
                88,
                Instant.parse("2026-06-15T00:00:00Z"),
                Instant.parse("2026-06-15T00:01:00Z"),
                null,
                Instant.parse("2026-06-15T00:00:00Z"),
                Instant.parse("2026-06-15T00:01:00Z"));
    }
}
