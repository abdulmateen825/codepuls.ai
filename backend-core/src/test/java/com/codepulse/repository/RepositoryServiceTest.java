package com.codepulse.repository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;
import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.repository.dto.CreateRepositoryRequest;
import com.codepulse.repository.dto.RepositoryResponse;

@ExtendWith(MockitoExtension.class)
class RepositoryServiceTest {

    @Mock
    private RepositoryRepository repositoryRepository;

    private RepositoryService repositoryService;

    @BeforeEach
    void setUp() {
        repositoryService = new RepositoryService(repositoryRepository);
    }

    @Test
    void createRepositoryNormalizesGithubUrlAndSavesForAuthenticatedOwner() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        when(repositoryRepository.existsByOwnerAndGithubOwnerIgnoreCaseAndGithubNameIgnoreCase(
                owner,
                "codepulse",
                "backend-core"))
                .thenReturn(false);
        when(repositoryRepository.save(any(RepositoryEntity.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        RepositoryResponse response = repositoryService.createRepository(
                new CreateRepositoryRequest("https://github.com/codepulse/backend-core.git"),
                owner);

        assertThat(response.repositoryUrl()).isEqualTo("https://github.com/codepulse/backend-core");
        assertThat(response.githubOwner()).isEqualTo("codepulse");
        assertThat(response.githubName()).isEqualTo("backend-core");

        ArgumentCaptor<RepositoryEntity> repositoryCaptor = ArgumentCaptor.forClass(RepositoryEntity.class);
        verify(repositoryRepository).save(repositoryCaptor.capture());
        assertThat(repositoryCaptor.getValue().getOwner()).isEqualTo(owner);
    }

    @Test
    void createRepositoryRejectsDuplicateRepositoryForOwner() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        when(repositoryRepository.existsByOwnerAndGithubOwnerIgnoreCaseAndGithubNameIgnoreCase(
                owner,
                "codepulse",
                "backend-core"))
                .thenReturn(true);

        assertThatThrownBy(() -> repositoryService.createRepository(
                new CreateRepositoryRequest("git@github.com:codepulse/backend-core.git"),
                owner))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("CONFLICT");

        verify(repositoryRepository, never()).save(any());
    }

    @Test
    void createRepositoryRejectsInvalidGithubUrl() {
        User owner = user(UUID.randomUUID(), "owner@example.com");

        assertThatThrownBy(() -> repositoryService.createRepository(
                new CreateRepositoryRequest("https://gitlab.com/codepulse/backend-core"),
                owner))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("BAD_REQUEST");
    }

    @Test
    void getRepositoriesReturnsOnlyCurrentOwnersRepositories() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        RepositoryEntity repository = repository(owner, "codepulse", "backend-core");
        when(repositoryRepository.findAllByOwnerOrderByCreatedAtDesc(owner)).thenReturn(List.of(repository));

        List<RepositoryResponse> responses = repositoryService.getRepositories(owner);

        assertThat(responses).hasSize(1);
        assertThat(responses.get(0).fullName()).isEqualTo("codepulse/backend-core");
    }

    @Test
    void getRepositoryReturnsRepositoryForOwner() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID repositoryId = UUID.randomUUID();
        RepositoryEntity repository = repository(owner, "codepulse", "backend-core");
        ReflectionTestUtils.setField(repository, "id", repositoryId);
        when(repositoryRepository.findById(repositoryId)).thenReturn(Optional.of(repository));

        RepositoryResponse response = repositoryService.getRepository(repositoryId, owner);

        assertThat(response.id()).isEqualTo(repositoryId);
        assertThat(response.fullName()).isEqualTo("codepulse/backend-core");
    }

    @Test
    void getRepositoryRejectsRepositoryOwnedByAnotherUser() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        User otherUser = user(UUID.randomUUID(), "other@example.com");
        UUID repositoryId = UUID.randomUUID();
        when(repositoryRepository.findById(repositoryId))
                .thenReturn(Optional.of(repository(otherUser, "codepulse", "backend-core")));

        assertThatThrownBy(() -> repositoryService.getRepository(repositoryId, owner))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("FORBIDDEN");
    }

    @Test
    void deleteRepositoryDeletesOwnedRepository() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID repositoryId = UUID.randomUUID();
        RepositoryEntity repository = repository(owner, "codepulse", "backend-core");
        when(repositoryRepository.findById(repositoryId)).thenReturn(Optional.of(repository));

        repositoryService.deleteRepository(repositoryId, owner);

        verify(repositoryRepository).delete(repository);
    }

    @Test
    void deleteRepositoryRejectsMissingRepository() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID repositoryId = UUID.randomUUID();
        when(repositoryRepository.findById(repositoryId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> repositoryService.deleteRepository(repositoryId, owner))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("NOT_FOUND");
    }

    @Test
    void createRepositoryRequiresAuthenticatedUser() {
        assertThatThrownBy(() -> repositoryService.createRepository(
                new CreateRepositoryRequest("https://github.com/codepulse/backend-core"),
                null))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("UNAUTHORIZED");
    }

    private User user(UUID id, String email) {
        User user = new User(email, "password-hash", "Test User");
        ReflectionTestUtils.setField(user, "id", id);
        return user;
    }

    private RepositoryEntity repository(User owner, String githubOwner, String githubName) {
        return new RepositoryEntity(
                owner,
                "https://github.com/" + githubOwner + "/" + githubName,
                githubOwner,
                githubName);
    }
}
