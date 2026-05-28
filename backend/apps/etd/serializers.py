from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import (
    Certainty,
    EtDAppraisal,
    EtDDomain,
    Judgement,
    ReferenceCitation,
)


class EtDDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtDDomain
        fields = ["id", "slug", "display_name_id", "display_name_en", "description", "prompt_text_id", "order"]
        read_only_fields = fields


class ReferenceCitationSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = ReferenceCitation
        fields = [
            "id",
            "reference_type",
            "citation_text",
            "authors",
            "publication_year",
            "title",
            "journal_name",
            "doi_pmid",
            "url",
            "evidence_summary",
            "created_at",
            "created_by",
        ]
        read_only_fields = ["id", "created_at", "created_by"]

    def validate_citation_text(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Sitasi tidak boleh kosong.")
        return value.strip()


class EtDAppraisalReadSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    domain_slug = serializers.CharField(source="domain.slug", read_only=True)
    judgement_label = serializers.SerializerMethodField()
    certainty_label = serializers.SerializerMethodField()
    references = ReferenceCitationSerializer(many=True, read_only=True)

    class Meta:
        model = EtDAppraisal
        fields = [
            "id",
            "case",
            "domain",
            "domain_slug",
            "member",
            "judgement",
            "judgement_label",
            "certainty",
            "certainty_label",
            "narrative",
            "references",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_judgement_label(self, obj: EtDAppraisal) -> str:
        return Judgement(obj.judgement).label

    def get_certainty_label(self, obj: EtDAppraisal) -> str:
        return Certainty(obj.certainty).label


class EtDAppraisalWriteSerializer(serializers.ModelSerializer):
    reference_ids = serializers.PrimaryKeyRelatedField(
        queryset=ReferenceCitation.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source="references",
    )

    class Meta:
        model = EtDAppraisal
        fields = ["judgement", "certainty", "narrative", "reference_ids"]

    def validate_judgement(self, value: int) -> int:
        if value not in {j.value for j in Judgement}:
            raise serializers.ValidationError("Nilai judgement tidak valid.")
        return value

    def validate(self, attrs: dict) -> dict:
        case = self.context.get("case")
        references = attrs.get("references") or []
        for ref in references:
            if ref.case_id != case.pk:
                raise serializers.ValidationError(
                    {"reference_ids": f"Referensi #{ref.pk} bukan milik kasus ini."}
                )
        return attrs


class DomainAggregateSerializer(serializers.Serializer):
    domain_slug = serializers.CharField()
    appraisal_count = serializers.IntegerField()
    mean_judgement = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    median_judgement = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    dominant_certainty = serializers.CharField(allow_null=True)
    certainty_score = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    combined_domain_score = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)


class OverallScoreSerializer(serializers.Serializer):
    domains_completed = serializers.IntegerField()
    domains_total = serializers.IntegerField()
    evidence_strength_score = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    average_certainty = serializers.CharField(allow_null=True)


class EtDSummarySerializer(serializers.Serializer):
    per_domain = DomainAggregateSerializer(many=True)
    overall = OverallScoreSerializer()
