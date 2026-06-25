package com.codepulse.ai;

import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.codepulse.ai.dto.FindingExplanationResponse;
import com.codepulse.ai.dto.RepositoryChatRequest;
import com.codepulse.ai.dto.RepositoryChatResponse;
import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;
import com.codepulse.integration.ai.AiServiceClient;
import com.codepulse.repository.RepositoryRepository;
import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.scan.FindingRepository;
import com.codepulse.scan.domain.FindingEntity;

@Service
public class AiInteractionService {

    private final RepositoryRepository repositoryRepository;
    private final FindingRepository findingRepository;
    private final AiServiceClient aiServiceClient;

    public AiInteractionService(
            RepositoryRepository repositoryRepository,
            FindingRepository findingRepository,
            AiServiceClient aiServiceClient) {
        this.repositoryRepository = repositoryRepository;
        this.findingRepository = findingRepository;
        this.aiServiceClient = aiServiceClient;
    }

    @Transactional(readOnly = true)
    public RepositoryChatResponse chat(UUID repositoryId, RepositoryChatRequest request, User currentUser) {
        requireAuthenticated(currentUser);
        RepositoryEntity repository = findRepositoryForAccess(repositoryId, currentUser);
        return aiServiceClient.chat(repository.getId(), request.question().trim(), request.normalizedHistory());
    }

    @Transactional(readOnly = true)
    public FindingExplanationResponse explainFinding(UUID findingId, User currentUser) {
        requireAuthenticated(currentUser);
        FindingEntity finding = findingRepository.findById(findingId)
                .orElseThrow(() -> ApiException.notFound("Finding was not found."));

        if (!finding.getScan().getRepository().getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this finding.");
        }

        return aiServiceClient.explainFinding(new AiServiceClient.InternalFindingExplainRequest(
                finding.getScan().getRepository().getId(),
                finding.getScan().getId(),
                finding.getId(),
                finding.getSeverity(),
                finding.getCategory(),
                finding.getTitle(),
                finding.getDescription(),
                finding.getRecommendation(),
                finding.getFilePath(),
                finding.getLineNumber(),
                finding.getStartLine(),
                finding.getEndLine(),
                finding.getSmellType(),
                finding.getLanguage(),
                finding.getCodeSnippet(),
                finding.getContextBefore(),
                finding.getContextAfter(),
                finding.getSuggestedRefactoring(),
                finding.getConfidence(),
                finding.getRuleId()));
    }

    private RepositoryEntity findRepositoryForAccess(UUID repositoryId, User currentUser) {
        RepositoryEntity repository = repositoryRepository.findById(repositoryId)
                .orElseThrow(() -> ApiException.notFound("Repository was not found."));

        if (!repository.getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this repository.");
        }

        return repository;
    }

    private void requireAuthenticated(User currentUser) {
        if (currentUser == null) {
            throw ApiException.unauthorized("Authentication is required.");
        }
    }
}
