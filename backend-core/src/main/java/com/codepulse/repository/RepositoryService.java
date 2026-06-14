package com.codepulse.repository;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;
import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.repository.dto.CreateRepositoryRequest;
import com.codepulse.repository.dto.RepositoryResponse;

@Service
public class RepositoryService {

    private static final Pattern SSH_GITHUB_PATTERN = Pattern.compile("^git@github\\.com:([^/]+)/(.+)$");

    private final RepositoryRepository repositoryRepository;

    public RepositoryService(RepositoryRepository repositoryRepository) {
        this.repositoryRepository = repositoryRepository;
    }

    @Transactional
    public RepositoryResponse createRepository(CreateRepositoryRequest request, User currentUser) {
        requireAuthenticated(currentUser);
        ParsedGithubRepository parsedRepository = parseGithubUrl(request.repositoryUrl());

        if (repositoryRepository.existsByOwnerAndGithubOwnerIgnoreCaseAndGithubNameIgnoreCase(
                currentUser,
                parsedRepository.owner(),
                parsedRepository.name())) {
            throw ApiException.conflict("Repository is already registered for this user.");
        }

        RepositoryEntity repository = repositoryRepository.save(new RepositoryEntity(
                currentUser,
                parsedRepository.normalizedUrl(),
                parsedRepository.owner(),
                parsedRepository.name()));

        return RepositoryResponse.from(repository);
    }

    @Transactional(readOnly = true)
    public List<RepositoryResponse> getRepositories(User currentUser) {
        requireAuthenticated(currentUser);

        return repositoryRepository.findAllByOwnerOrderByCreatedAtDesc(currentUser)
                .stream()
                .map(RepositoryResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public RepositoryResponse getRepository(UUID id, User currentUser) {
        requireAuthenticated(currentUser);

        RepositoryEntity repository = repositoryRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Repository was not found."));

        enforceOwnership(repository, currentUser);
        return RepositoryResponse.from(repository);
    }

    @Transactional
    public void deleteRepository(UUID id, User currentUser) {
        requireAuthenticated(currentUser);

        RepositoryEntity repository = repositoryRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Repository was not found."));

        enforceOwnership(repository, currentUser);
        repositoryRepository.delete(repository);
    }

    private void requireAuthenticated(User currentUser) {
        if (currentUser == null) {
            throw ApiException.unauthorized("Authentication is required.");
        }
    }

    private void enforceOwnership(RepositoryEntity repository, User currentUser) {
        if (!repository.getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this repository.");
        }
    }

    private ParsedGithubRepository parseGithubUrl(String repositoryUrl) {
        String trimmedUrl = repositoryUrl.trim();
        Matcher sshMatcher = SSH_GITHUB_PATTERN.matcher(trimmedUrl);

        if (sshMatcher.matches()) {
            return createParsedRepository(sshMatcher.group(1), sshMatcher.group(2));
        }

        try {
            URI uri = new URI(trimmedUrl);
            String host = uri.getHost();

            if (host == null || !"github.com".equalsIgnoreCase(host)) {
                throw invalidRepositoryUrl();
            }

            String path = uri.getPath();
            if (path == null) {
                throw invalidRepositoryUrl();
            }

            String[] segments = path.replaceFirst("^/", "").split("/");
            if (segments.length != 2) {
                throw invalidRepositoryUrl();
            }

            return createParsedRepository(segments[0], segments[1]);
        } catch (URISyntaxException exception) {
            throw invalidRepositoryUrl();
        }
    }

    private ParsedGithubRepository createParsedRepository(String rawOwner, String rawName) {
        String owner = rawOwner.trim();
        String name = rawName.trim().replaceFirst("\\.git$", "");

        if (!isValidGithubSegment(owner) || !isValidGithubSegment(name)) {
            throw invalidRepositoryUrl();
        }

        return new ParsedGithubRepository(
                owner,
                name,
                "https://github.com/" + owner + "/" + name);
    }

    private boolean isValidGithubSegment(String value) {
        return value.length() <= 120
                && value.matches("[A-Za-z0-9._-]+")
                && !value.toLowerCase(Locale.ROOT).endsWith(".git");
    }

    private ApiException invalidRepositoryUrl() {
        return ApiException.badRequest("Repository URL must be a valid GitHub repository URL.");
    }

    private record ParsedGithubRepository(String owner, String name, String normalizedUrl) {
    }
}
