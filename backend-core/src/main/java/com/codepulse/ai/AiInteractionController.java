package com.codepulse.ai;

import java.util.UUID;

import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.codepulse.ai.dto.FindingExplanationResponse;
import com.codepulse.ai.dto.RepositoryChatRequest;
import com.codepulse.ai.dto.RepositoryChatResponse;
import com.codepulse.auth.entity.User;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api")
public class AiInteractionController {

    private final AiInteractionService aiInteractionService;

    public AiInteractionController(AiInteractionService aiInteractionService) {
        this.aiInteractionService = aiInteractionService;
    }

    @PostMapping("/repositories/{repositoryId}/chat")
    public RepositoryChatResponse chat(
            @PathVariable UUID repositoryId,
            @Valid @RequestBody RepositoryChatRequest request,
            @AuthenticationPrincipal User currentUser) {
        return aiInteractionService.chat(repositoryId, request, currentUser);
    }

    @PostMapping("/findings/{findingId}/explain")
    public FindingExplanationResponse explainFinding(
            @PathVariable UUID findingId,
            @AuthenticationPrincipal User currentUser) {
        return aiInteractionService.explainFinding(findingId, currentUser);
    }
}
