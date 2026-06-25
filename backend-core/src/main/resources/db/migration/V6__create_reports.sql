create table reports (
    id uuid primary key,
    scan_id uuid not null,
    file_name varchar(255) not null,
    content_type varchar(120) not null,
    size_bytes bigint not null,
    content bytea not null,
    created_at timestamp with time zone not null,
    constraint fk_reports_scan
        foreign key (scan_id)
        references scans (id)
        on delete cascade
);

create index idx_reports_scan_created_at
    on reports (scan_id, created_at desc);
