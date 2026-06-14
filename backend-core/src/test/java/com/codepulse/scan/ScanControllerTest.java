package com.codepulse.scan;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.ArgumentMatchers.nullable;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.security.oauth2.client.OAuth2ClientAutoConfiguration;
import org.springframework.boot.autoconfigure.security.oauth2.client.servlet.OAuth2ClientWebSecurityAutoConfiguration;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;

import com.codepulse.auth.entity.User;
import com.codepulse.auth.service.JwtService;
import com.codepulse.common.exception.ApiException;
import com.codepulse.scan.dto.FindingPageResponse;
import com.codepulse.scan.dto.FindingResponse;
import com.codepulse.scan.dto.ScanDetailResponse;
import com.codepulse.scan.dto.ScanSummaryResponse;

@WebMvcTest(
        controllers = ScanController.class,
        excludeAutoConfiguration = {
                OAuth2ClientAutoConfiguration.class,
                OAuth2ClientWebSecurityAutoConfiguration.class
        })
class ScanControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ScanService scanService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserDetailsService userDetailsService;

    @Test
    void startScanReturnsCreatedScanForAuthenticatedUser() throws Exception {
        UUID repositoryId = UUID.randomUUID();
        UUID scanId = UUID.randomUUID();
        when(scanService.startScan(eq(repositoryId), nullable(User.class)))
                .thenReturn(scanDetail(scanId, repositoryId));

        mockMvc.perform(post("/api/repositories/{repositoryId}/scans", repositoryId)
                .with(csrf())
                .with(user(currentUser())))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(scanId.toString()))
                .andExpect(jsonPath("$.status").value("QUEUED"));
    }

    @Test
    void startScanRequiresAuthentication() throws Exception {
        mockMvc.perform(post("/api/repositories/{repositoryId}/scans", UUID.randomUUID())
                .with(csrf()))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void startScanReturnsForbiddenForRepositoryOwnedByAnotherUser() throws Exception {
        UUID repositoryId = UUID.randomUUID();
        when(scanService.startScan(eq(repositoryId), nullable(User.class)))
                .thenThrow(ApiException.forbidden("You do not have access to this repository."));

        mockMvc.perform(post("/api/repositories/{repositoryId}/scans", repositoryId)
                .with(csrf())
                .with(user(currentUser())))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value("FORBIDDEN"));
    }

    @Test
    void startScanRejectsInvalidRepositoryId() throws Exception {
        mockMvc.perform(post("/api/repositories/{repositoryId}/scans", "not-a-uuid")
                .with(csrf())
                .with(user(currentUser())))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getRepositoryScansReturnsSummaries() throws Exception {
        UUID repositoryId = UUID.randomUUID();
        UUID scanId = UUID.randomUUID();
        when(scanService.getRepositoryScans(eq(repositoryId), nullable(User.class)))
                .thenReturn(List.of(scanSummary(scanId, repositoryId)));

        mockMvc.perform(get("/api/repositories/{repositoryId}/scans", repositoryId)
                .with(user(currentUser())))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(scanId.toString()))
                .andExpect(jsonPath("$[0].repositoryFullName").value("codepulse/backend-core"));
    }

    @Test
    void getScanReturnsNotFoundWhenMissing() throws Exception {
        UUID scanId = UUID.randomUUID();
        when(scanService.getScan(eq(scanId), nullable(User.class)))
                .thenThrow(ApiException.notFound("Scan was not found."));

        mockMvc.perform(get("/api/scans/{scanId}", scanId)
                .with(user(currentUser())))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("NOT_FOUND"));
    }

    @Test
    void getFindingsReturnsPagedFindings() throws Exception {
        UUID scanId = UUID.randomUUID();
        FindingResponse finding = finding(scanId);
        when(scanService.getFindings(
                eq(scanId),
                eq("HIGH"),
                eq("SECURITY"),
                any(Pageable.class),
                nullable(User.class)))
                .thenReturn(new FindingPageResponse(List.of(finding), 1, 1, 0, 20));

        mockMvc.perform(get("/api/scans/{scanId}/findings", scanId)
                .param("severity", "HIGH")
                .param("category", "SECURITY")
                .with(user(currentUser())))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].severity").value("HIGH"))
                .andExpect(jsonPath("$.totalElements").value(1));
    }

    @Test
    void getFindingsAllowsMissingOptionalFilters() throws Exception {
        UUID scanId = UUID.randomUUID();
        when(scanService.getFindings(
                eq(scanId),
                isNull(),
                isNull(),
                any(Pageable.class),
                nullable(User.class)))
                .thenReturn(new FindingPageResponse(List.of(), 0, 0, 0, 20));

        mockMvc.perform(get("/api/scans/{scanId}/findings", scanId)
                .with(user(currentUser())))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(0));
    }

    private User currentUser() {
        User user = new User("owner@example.com", "password-hash", "Owner User");
        ReflectionTestUtils.setField(user, "id", UUID.randomUUID());
        return user;
    }

    private ScanDetailResponse scanDetail(UUID scanId, UUID repositoryId) {
        return new ScanDetailResponse(
                scanId,
                repositoryId,
                "https://github.com/codepulse/backend-core",
                "codepulse/backend-core",
                "QUEUED",
                null,
                null,
                null,
                null,
                null,
                null,
                Instant.parse("2026-06-15T00:00:00Z"),
                Instant.parse("2026-06-15T00:00:00Z"));
    }

    private ScanSummaryResponse scanSummary(UUID scanId, UUID repositoryId) {
        return new ScanSummaryResponse(
                scanId,
                repositoryId,
                "codepulse/backend-core",
                "QUEUED",
                null,
                null,
                null,
                null,
                null,
                Instant.parse("2026-06-15T00:00:00Z"));
    }

    private FindingResponse finding(UUID scanId) {
        return new FindingResponse(
                UUID.randomUUID(),
                scanId,
                "java:S001",
                "SECURITY",
                "HIGH",
                "Avoid hardcoded secrets",
                "A hardcoded secret was found.",
                "src/main/java/App.java",
                42,
                "String secret = \"value\";",
                "Move secrets into managed configuration.",
                Instant.parse("2026-06-15T00:00:00Z"));
    }
}
