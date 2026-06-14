package com.codepulse.repository;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.nullable;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.security.oauth2.client.OAuth2ClientAutoConfiguration;
import org.springframework.boot.autoconfigure.security.oauth2.client.servlet.OAuth2ClientWebSecurityAutoConfiguration;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;

import com.codepulse.auth.entity.User;
import com.codepulse.auth.service.JwtService;
import com.codepulse.common.exception.ApiException;
import com.codepulse.repository.dto.CreateRepositoryRequest;
import com.codepulse.repository.dto.RepositoryResponse;
import com.fasterxml.jackson.databind.ObjectMapper;

@WebMvcTest(
        controllers = RepositoryController.class,
        excludeAutoConfiguration = {
                OAuth2ClientAutoConfiguration.class,
                OAuth2ClientWebSecurityAutoConfiguration.class
        })
class RepositoryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private RepositoryService repositoryService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserDetailsService userDetailsService;

    @Test
    void createRepositoryReturnsCreatedRepositoryForAuthenticatedUser() throws Exception {
        RepositoryResponse response = response(UUID.randomUUID(), "codepulse", "backend-core");
        when(repositoryService.createRepository(any(CreateRepositoryRequest.class), nullable(User.class)))
                .thenReturn(response);

        mockMvc.perform(post("/api/repositories")
                .with(csrf())
                .with(user(currentUser()))
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(new CreateRepositoryRequest(
                        "https://github.com/codepulse/backend-core"))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(response.id().toString()))
                .andExpect(jsonPath("$.repositoryUrl").value("https://github.com/codepulse/backend-core"))
                .andExpect(jsonPath("$.fullName").value("codepulse/backend-core"));
    }

    @Test
    void createRepositoryRejectsValidationErrors() throws Exception {
        mockMvc.perform(post("/api/repositories")
                .with(csrf())
                .with(user(currentUser()))
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(new CreateRepositoryRequest(""))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"))
                .andExpect(jsonPath("$.details.repositoryUrl").value("Repository URL is required"));
    }

    @Test
    void getRepositoriesRequiresAuthentication() throws Exception {
        mockMvc.perform(get("/api/repositories"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void getRepositoriesReturnsAuthenticatedUsersRepositories() throws Exception {
        RepositoryResponse response = response(UUID.randomUUID(), "codepulse", "backend-core");
        when(repositoryService.getRepositories(nullable(User.class))).thenReturn(List.of(response));

        mockMvc.perform(get("/api/repositories")
                .with(user(currentUser())))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].fullName").value("codepulse/backend-core"));
    }

    @Test
    void getRepositoryReturnsForbiddenWhenServiceRejectsOwnership() throws Exception {
        UUID repositoryId = UUID.randomUUID();
        when(repositoryService.getRepository(eq(repositoryId), nullable(User.class)))
                .thenThrow(ApiException.forbidden("You do not have access to this repository."));

        mockMvc.perform(get("/api/repositories/{id}", repositoryId)
                .with(user(currentUser())))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value("FORBIDDEN"));
    }

    @Test
    void getRepositoryReturnsNotFoundWhenMissing() throws Exception {
        UUID repositoryId = UUID.randomUUID();
        when(repositoryService.getRepository(eq(repositoryId), nullable(User.class)))
                .thenThrow(ApiException.notFound("Repository was not found."));

        mockMvc.perform(get("/api/repositories/{id}", repositoryId)
                .with(user(currentUser())))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("NOT_FOUND"));
    }

    @Test
    void deleteRepositoryReturnsNoContent() throws Exception {
        mockMvc.perform(delete("/api/repositories/{id}", UUID.randomUUID())
                .with(csrf())
                .with(user(currentUser())))
                .andExpect(status().isNoContent());
    }

    @Test
    void deleteRepositoryReturnsForbiddenWhenServiceRejectsOwnership() throws Exception {
        UUID repositoryId = UUID.randomUUID();
        doThrow(ApiException.forbidden("You do not have access to this repository."))
                .when(repositoryService)
                .deleteRepository(eq(repositoryId), nullable(User.class));

        mockMvc.perform(delete("/api/repositories/{id}", repositoryId)
                .with(csrf())
                .with(user(currentUser())))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value("FORBIDDEN"));
    }

    private User currentUser() {
        User user = new User("owner@example.com", "password-hash", "Owner User");
        ReflectionTestUtils.setField(user, "id", UUID.randomUUID());
        return user;
    }

    private RepositoryResponse response(UUID id, String githubOwner, String githubName) {
        return new RepositoryResponse(
                id,
                "https://github.com/" + githubOwner + "/" + githubName,
                githubOwner,
                githubName,
                githubOwner + "/" + githubName,
                "ACTIVE",
                Instant.parse("2026-06-15T00:00:00Z"),
                Instant.parse("2026-06-15T00:00:00Z"));
    }
}
