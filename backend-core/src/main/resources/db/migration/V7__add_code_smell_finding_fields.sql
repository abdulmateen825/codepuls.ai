alter table findings
    add column start_line integer,
    add column end_line integer,
    add column smell_type varchar(80),
    add column language varchar(40),
    add column evidence_json jsonb,
    add column metrics_json jsonb,
    add column context_before varchar(4000),
    add column context_after varchar(4000),
    add column suggested_refactoring varchar(2000),
    add column confidence double precision;

alter table findings
    add constraint ck_findings_start_line
        check (start_line is null or start_line > 0),
    add constraint ck_findings_end_line
        check (end_line is null or start_line is null or end_line >= start_line),
    add constraint ck_findings_confidence
        check (confidence is null or (confidence >= 0 and confidence <= 1)),
    add constraint ck_findings_smell_type
        check (
            smell_type is null
            or smell_type in (
                'LONG_METHOD',
                'LARGE_CLASS',
                'HIGH_CYCLOMATIC_COMPLEXITY',
                'DEEP_NESTING',
                'LONG_PARAMETER_LIST',
                'DUPLICATED_CODE',
                'DEAD_CODE',
                'GOD_OBJECT'
            )
        );

create index idx_findings_scan_rule_id
    on findings (scan_id, rule_id);

create index idx_findings_scan_smell_type
    on findings (scan_id, smell_type);

create index idx_findings_scan_language
    on findings (scan_id, language);

create index idx_findings_scan_file_path
    on findings (scan_id, file_path);
