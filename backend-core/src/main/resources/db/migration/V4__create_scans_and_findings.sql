create table scans (
    id uuid primary key,
    repository_id uuid not null,
    status varchar(30) not null,
    quality_score integer,
    security_score integer,
    maintainability_score integer,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    error_message varchar(1000),
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    constraint fk_scans_repository
        foreign key (repository_id)
        references repositories (id)
        on delete cascade,
    constraint ck_scans_quality_score
        check (quality_score is null or (quality_score >= 0 and quality_score <= 100)),
    constraint ck_scans_security_score
        check (security_score is null or (security_score >= 0 and security_score <= 100)),
    constraint ck_scans_maintainability_score
        check (maintainability_score is null or (maintainability_score >= 0 and maintainability_score <= 100))
);

create table findings (
    id uuid primary key,
    scan_id uuid not null,
    rule_id varchar(120) not null,
    category varchar(50) not null,
    severity varchar(30) not null,
    title varchar(300) not null,
    description varchar(2000) not null,
    file_path varchar(1000) not null,
    line_number integer,
    code_snippet varchar(4000),
    recommendation varchar(2000),
    created_at timestamp with time zone not null,
    constraint fk_findings_scan
        foreign key (scan_id)
        references scans (id)
        on delete cascade,
    constraint ck_findings_line_number
        check (line_number is null or line_number > 0)
);

create index idx_scans_repository_created_at
    on scans (repository_id, created_at desc);

create index idx_scans_status
    on scans (status);

create index idx_findings_scan_created_at
    on findings (scan_id, created_at desc);

create index idx_findings_scan_severity
    on findings (scan_id, severity);

create index idx_findings_scan_category
    on findings (scan_id, category);
