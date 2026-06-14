package com.codepulse.repository;

import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.codepulse.auth.entity.User;
import com.codepulse.repository.dto.CreateRepositoryRequest;
import com.codepulse.repository.dto.RepositoryResponse;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/repositories")
public class RepositoryController {

    private final RepositoryService repositoryService;

    public RepositoryController(RepositoryService repositoryService) {
        this.repositoryService = repositoryService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public RepositoryResponse createRepository(
            @Valid @RequestBody CreateRepositoryRequest request,
            @AuthenticationPrincipal User currentUser) {
        return repositoryService.createRepository(request, currentUser);
    }

    @GetMapping
    public List<RepositoryResponse> getRepositories(@AuthenticationPrincipal User currentUser) {
        return repositoryService.getRepositories(currentUser);
    }

    @GetMapping("/{id}")
    public RepositoryResponse getRepository(
            @PathVariable UUID id,
            @AuthenticationPrincipal User currentUser) {
        return repositoryService.getRepository(id, currentUser);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteRepository(
            @PathVariable UUID id,
            @AuthenticationPrincipal User currentUser) {
        repositoryService.deleteRepository(id, currentUser);
    }
}
