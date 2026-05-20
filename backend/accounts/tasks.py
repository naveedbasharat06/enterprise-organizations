import os
from celery import shared_task
from django.conf import settings


# ── Audio / Transcription helpers ─────────────────────────────────────────────

def _extract_audio(video_path):
    """
    Extract compact mono audio from any video/audio file using the bundled ffmpeg binary.
    32 kbps mono MP3 at 16 kHz → ~12 MB/hour, well within Groq's 25 MB limit.
    """
    import subprocess
    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    audio_path = os.path.splitext(video_path)[0] + '_audio.mp3'

    probe = subprocess.run([ffmpeg, '-i', video_path], capture_output=True, text=True)
    if 'Audio:' not in probe.stderr:
        raise ValueError(
            'This file has no audio track. '
            'For screen recordings, make sure to allow microphone access when recording.'
        )

    cmd = [
        ffmpeg, '-y',
        '-i', video_path,
        '-vn',
        '-ac', '1',
        '-ar', '16000',
        '-ab', '32k',
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f'Audio extraction failed: {result.stderr[-400:]}')
    return audio_path


def _transcribe_video(video_path):
    """Extract audio then transcribe via Groq's free Whisper API."""
    import openai

    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        raise ValueError('GROQ_API_KEY is not configured. Add it to your .env file.')

    audio_path = _extract_audio(video_path)
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1',
        )
        with open(audio_path, 'rb') as f:
            result = client.audio.transcriptions.create(
                model='whisper-large-v3',
                file=f,
                response_format='verbose_json',
                timestamp_granularities=['segment'],
            )
        return [
            {'start': seg.start, 'end': seg.end, 'text': seg.text.strip()}
            for seg in result.segments
        ]
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


def _format_timestamp(seconds):
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _group_segments(segments, interval=30):
    """Merge Whisper's 1-3s segments into ~30s blocks (Otter.ai / Rev.com style)."""
    if not segments:
        return []
    groups = []
    block_start = segments[0]['start']
    block_texts = []
    for seg in segments:
        if seg['start'] - block_start >= interval and block_texts:
            groups.append({'start': block_start, 'text': ' '.join(block_texts)})
            block_start = seg['start']
            block_texts = []
        block_texts.append(seg['text'])
    if block_texts:
        groups.append({'start': block_start, 'text': ' '.join(block_texts)})
    return groups


def _generate_pdf(recording):
    """
    Build a professional timestamped transcript PDF — one timestamp per 30-second
    block, matching the format used by Rev.com, Otter.ai, and Zoom transcripts.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    )

    ACCENT   = colors.HexColor('#6C63FF')
    GRAY     = colors.HexColor('#6B7280')
    LIGHT_BG = colors.HexColor('#F3F4F6')

    pdf_rel = f'transcripts/recording_{recording.id}.pdf'
    pdf_abs = os.path.join(settings.MEDIA_ROOT, pdf_rel)
    os.makedirs(os.path.dirname(pdf_abs), exist_ok=True)

    doc = SimpleDocTemplate(
        pdf_abs, pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )
    styles = getSampleStyleSheet()

    brand_style = ParagraphStyle(
        'Brand', parent=styles['Normal'],
        fontSize=9, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=2,
    )
    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=22, fontName='Helvetica-Bold', spaceAfter=4, leading=26,
    )
    meta_style = ParagraphStyle(
        'Meta', parent=styles['Normal'],
        fontSize=9, textColor=GRAY, leading=14,
    )
    section_style = ParagraphStyle(
        'Section', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', textColor=ACCENT,
        spaceBefore=14, spaceAfter=6,
    )
    ts_style = ParagraphStyle(
        'TS', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold', textColor=ACCENT,
        spaceBefore=12, spaceAfter=2,
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=11, leading=18, spaceAfter=0,
    )
    full_style = ParagraphStyle(
        'Full', parent=styles['Normal'],
        fontSize=11, leading=19, spaceAfter=0,
    )

    segments = (recording.transcript_data or {}).get('segments', [])
    groups   = _group_segments(segments, interval=30)
    full_text = ' '.join(s['text'] for s in segments)

    duration_secs = int(segments[-1]['end']) if segments else 0
    duration_str  = _format_timestamp(duration_secs)
    word_count    = len(full_text.split())

    story = []

    story.append(Paragraph('RoleBase', brand_style))
    story.append(Paragraph(recording.title or 'Screen Recording', title_style))
    story.append(HRFlowable(width='100%', thickness=1, color=LIGHT_BG, spaceAfter=8))

    meta_data = [
        ['Date',         recording.created_at.strftime('%B %d, %Y  %H:%M UTC')],
        ['Recorded by',  recording.user.username],
        ['Duration',     duration_str],
        ['Word count',   f'{word_count:,}'],
        ['Organization', recording.organization.name if recording.organization else '—'],
    ]
    tbl = Table(meta_data, colWidths=[35*mm, 120*mm])
    tbl.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('TEXTCOLOR',     (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR',     (1, 0), (1, -1), colors.black),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10*mm))

    story.append(Paragraph('TIMESTAMPED TRANSCRIPT', section_style))
    story.append(HRFlowable(width='100%', thickness=0.5, color=LIGHT_BG, spaceAfter=4))

    if not groups:
        story.append(Paragraph('No transcript data available.', body_style))
    else:
        for grp in groups:
            story.append(Paragraph(f"[{_format_timestamp(grp['start'])}]", ts_style))
            story.append(Paragraph(grp['text'], body_style))

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph('FULL TRANSCRIPT', section_style))
    story.append(HRFlowable(width='100%', thickness=0.5, color=LIGHT_BG, spaceAfter=6))
    story.append(Paragraph(full_text or 'No transcript data available.', full_style))

    doc.build(story)
    return pdf_rel


# ── Celery Task ───────────────────────────────────────────────────────────────

def _track_storage(recording, video_size_mb, pdf_size_mb):
    """Record storage usage and report overage to Stripe if needed."""
    from .models import StorageUsage
    from payments.stripe_utils import report_storage_usage

    org = recording.organization
    if not org:
        return

    total_mb = video_size_mb + pdf_size_mb

    StorageUsage.objects.create(
        organization=org,
        recording=recording,
        file_size_mb=video_size_mb,
        file_type=StorageUsage.FILE_RECORDING,
    )
    if pdf_size_mb > 0:
        StorageUsage.objects.create(
            organization=org,
            recording=recording,
            file_size_mb=pdf_size_mb,
            file_type=StorageUsage.FILE_TRANSCRIPT,
        )

    org.storage_used_mb = (org.storage_used_mb or 0) + total_mb
    org.save(update_fields=['storage_used_mb'])

    # Report overage to Stripe if allowance exceeded
    overage_mb = max(0, org.storage_used_mb - org.storage_included_mb)
    if overage_mb > 0 and org.stripe_customer_id:
        unreported = StorageUsage.objects.filter(organization=org, reported_to_stripe=False)
        unreported_mb = sum(r.file_size_mb for r in unreported)
        if unreported_mb > 0:
            try:
                report_storage_usage(org.stripe_customer_id, org.plan, unreported_mb)
                unreported.update(reported_to_stripe=True)
            except Exception:
                pass


@shared_task(bind=True, name='accounts.tasks.process_recording')
def process_recording(self, recording_id):
    """
    Background task: transcribe a recording and generate a PDF transcript.
    Called immediately after the video file is saved; the HTTP response is
    already sent to the browser with status=pending by the time this runs.
    """
    from .models import Recording

    try:
        recording = Recording.objects.select_related('user', 'organization').get(id=recording_id)
    except Recording.DoesNotExist:
        return

    recording.status = Recording.STATUS_PROCESSING
    recording.save(update_fields=['status'])

    try:
        segments = _transcribe_video(recording.video_file.path)
        recording.transcript_data = {'segments': segments}
        recording.pdf_file = _generate_pdf(recording)
        recording.status = Recording.STATUS_DONE
        recording.error_message = ''
        recording.save()

        # Track storage usage for billing
        try:
            video_size_mb = os.path.getsize(recording.video_file.path) / (1024 * 1024)
            pdf_size_mb = 0
            if recording.pdf_file:
                pdf_path = os.path.join(os.path.dirname(recording.video_file.path),
                                        '..', recording.pdf_file.name)
                pdf_path = os.path.normpath(os.path.join(
                    os.path.dirname(recording.video_file.path), '..', '..', recording.pdf_file.name
                ))
                if os.path.exists(pdf_path):
                    pdf_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            _track_storage(recording, video_size_mb, pdf_size_mb)
        except Exception:
            pass
    except Exception as exc:
        recording.status = Recording.STATUS_FAILED
        recording.error_message = str(exc)
        recording.save()
