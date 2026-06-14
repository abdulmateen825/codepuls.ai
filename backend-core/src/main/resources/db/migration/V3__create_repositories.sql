create table repositories (
    id uuid primary key,
    owner_id uuid not null,
    github_url varchar(500) not null,
    github_owner varchar(120) not null,
    github_name varchar(120) not null,
    status varchar(30) not null,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    constraint fk_repositories_owner
        foreign key (owner_id)
        references users (id)
        on delete cascade,
    constraint uk_repositories_owner_github_repo
        unique (owner_id, github_owner, github_name)
);

create index idx_repositories_owner_created_at
    on repositories (owner_id, created_at desc);

create index idx_repositories_status
    on repositories (status);
