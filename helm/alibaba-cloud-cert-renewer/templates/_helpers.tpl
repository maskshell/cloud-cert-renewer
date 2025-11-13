{{/*
Expand the name of the chart.
*/}}
{{- define "alibaba-cloud-cert-renewer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "alibaba-cloud-cert-renewer.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "alibaba-cloud-cert-renewer.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "alibaba-cloud-cert-renewer.labels" -}}
helm.sh/chart: {{ include "alibaba-cloud-cert-renewer.chart" . }}
{{ include "alibaba-cloud-cert-renewer.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.labels }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "alibaba-cloud-cert-renewer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "alibaba-cloud-cert-renewer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Reloader annotations
*/}}
{{- define "alibaba-cloud-cert-renewer.reloaderAnnotations" -}}
{{- if .Values.reloader.enabled }}
{{- if .Values.reloader.auto }}
reloader.stakater.com/auto: "{{ .Values.reloader.auto }}"
{{- end }}
{{- if .Values.reloader.search }}
reloader.stakater.com/search: "{{ .Values.reloader.search }}"
{{- end }}
{{- end }}
{{- end }}

