package com.codepulse.ai;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import com.codepulse.ai.dto.RepositoryChatRequest;
import com.codepulse.ai.dto.RepositoryChatResponse;
import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;
import com.codepulse.integration.ai.AiServiceClient;
import com.codepulse.repository.RepositoryRepository;
import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.scan.FindingRepository;
import com.codepulse.scan.domain.FindingEntity;
import com.codepulse.scan.domain.ScanEntity;

@ExtendWith(MockitoExtension.class)
class AiInteractionServiceTest {

    @Mock
    private RepositoryRepository repositoryRepository;

    @Mock
    private FindingRepository findingRepository;

    @Mock
    private AiServiceClient aiServiceClient;

    private AiInteractionService service;

    @BeforeEach
    void setUp() {
        service = new AiInteractionService(repositoryRepository, findingRepository, aiServiceClient);
    }

    @Test
    void chatValidatesRepositoryOwnershipBeforeCallingFastApi() {
        User owner = user(UUID.randomUUID());
        RepositoryEntity repository = repository(UUID.randomUUID(), owner);
        RepositoryChatRequest request = new RepositoryChatRequest("Where is auth handled?", List.of());
        when(repositoryRepository.findById(repository.getId())).thenReturn(Optional.of(repository));
        when(aiServiceClient.chat(repository.getId(), request.question(), List.of()))
                .thenReturn(new RepositoryChatResponse("answer", List.of(), List.of()));

        RepositoryChatResponse response = service.chat(repository.getId(), request, owner);

        assertThat(response.answer()).isEqualTo("answer");
        verify(aiServiceClient).chat(repository.getId(), request.question(), List.of());
    }

    @Test
    void chatRejectsRepositoryOwnedByAnotherUser() {
        User owner = user(UUID.randomUUID());
        User other = user(UUID.randomUUID());
        RepositoryEntity repository = repository(UUID.randomUUID(), other);
        when(repositoryRepository.findById(repository.getId())).thenReturn(Optional.of(repository));

        assertThatThrownBy(() -> service.chat(repository.getId(), new RepositoryChatRequest("question", List.of()), owner))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("FORBIDDEN");
    }

    @Test
    void explainFindingValidatesFindingOwnershipBeforeCallingFastApi() {
        User owner = user(UUID.randomUUID());
        RepositoryEntity repository = repository(UUID.randomUUID(), owner);
        ScanEntity scan = new ScanEntity(repository);
        ReflectionTestUtils.setField(scan, "id", UUID.randomUUID());
        FindingEntity finding = finding(UUID.randomUUID(), scan);
        when(findingRepository.findById(finding.getId())).thenReturn(Optional.of(finding));

        service.explainFinding(finding.getId(), owner);

        verify(aiServiceClient).explainFinding(org.mockito.ArgumentMatchers.argThat(request ->
                request.findingId().equals(finding.getId())
                        && request.repositoryId().equals(repository.getId())
                        && request.scanId().equals(scan.getId())));
    }

    private User user(UUID id) {
        User user = new User("user@example.com", "password", "User");
        ReflectionTestUtils.setField(user, "id", id);
        return user;
    }

    private RepositoryEntity repository(UUID id, User owner) {
        RepositoryEntity repository = new RepositoryEntity(
                owner,
                "https://github.com/codepulse/backend-core",
                "codepulse",
                "backend-core");
        ReflectionTestUtils.setField(repository, "id", id);
        return repository;
    }

    private FindingEntity finding(UUID id, ScanEntity scan) {
        FindingEntity finding = new FindingEntity(
                scan,
                "ruff:F401",
                "quality",
                "HIGH",
                "Unused import",
                "Imported symbol is unused.",
                "app.py",
                7,
                null,
                "Remove the import.");
        ReflectionTestUtils.setField(finding, "id", id);
        return finding;
    }
}
