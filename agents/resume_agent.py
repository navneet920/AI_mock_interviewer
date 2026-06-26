import json
import re
from ast import literal_eval

from prompts.resume_prompt import build_resume_prompt


class ResumeAgent:

    def __init__(self, llm):
        self.llm = llm

    def _empty_resume_data(self):
        return {
            "name": "",
            "summary": "",
            "skills": [],
            "education": [],
            "projects": [],
            "internship": [],
            "certifications": [],
            "achievements": []
        }

    def _extract_json_content(self, content: str) -> str:
        content = content.strip()
        content = re.sub(
            r"<think>.*?</think>",
            "",
            content,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()

        fenced_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            content,
            flags=re.DOTALL | re.IGNORECASE
        )
        if fenced_match:
            return fenced_match.group(1).strip()

        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1].strip()

        return content

    def _load_json_content(self, content: str) -> dict:
        content = self._extract_json_content(content)
        content = re.sub(r",\s*([}\]])", r"\1", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        try:
            parsed = literal_eval(content)
        except (SyntaxError, ValueError):
            raise

        if not isinstance(parsed, dict):
            raise ValueError("Resume parser response is not a JSON object")

        return parsed

    def _as_text_list(self, value):
        if value is None or value == "":
            return []

        if isinstance(value, list):
            items = value
        else:
            items = [value]

        normalized = []

        for item in items:
            if isinstance(item, dict):
                text = ", ".join(str(v) for v in item.values() if v)
            else:
                text = str(item)

            text = text.strip()

            if text:
                normalized.append(text)

        return normalized

    def _normalize_resume_data(self, data: dict) -> dict:
        empty_data = self._empty_resume_data()

        if not isinstance(data, dict):
            return empty_data

        aliases = {
            "internships": "internship",
            "experience": "internship",
            "work_experience": "internship",
            "workExperience": "internship",
            "certificates": "certifications",
            "certificate": "certifications",
            "technical_skills": "skills",
            "technicalSkills": "skills",
            "project": "projects"
        }

        for source_key, target_key in aliases.items():
            if target_key not in data and source_key in data:
                data[target_key] = data[source_key]

        normalized = empty_data.copy()
        normalized["name"] = str(data.get("name") or "").strip()
        normalized["summary"] = str(data.get("summary") or "").strip()

        for key in (
            "skills",
            "education",
            "projects",
            "internship",
            "certifications",
            "achievements"
        ):
            normalized[key] = self._as_text_list(data.get(key))

        return normalized

    def _merge_resume_data(self, primary: dict, fallback: dict) -> dict:
        merged = self._normalize_resume_data(primary)
        fallback = self._normalize_resume_data(fallback)

        for key, fallback_value in fallback.items():
            if key in ("name", "summary"):
                if not merged[key] and fallback_value:
                    merged[key] = fallback_value
            elif not merged[key] and fallback_value:
                merged[key] = fallback_value

        return merged

    def _has_resume_data(self, data: dict) -> bool:
        return any(
            data.get(key)
            for key in (
                "name",
                "summary",
                "skills",
                "education",
                "projects",
                "internship",
                "certifications",
                "achievements"
            )
        )

    def _section_lines(self, resume_text: str, headings: tuple[str, ...]) -> list[str]:
        all_headings = (
            "summary",
            "objective",
            "skills",
            "technical skills",
            "education",
            "projects",
            "project",
            "experience",
            "internship",
            "internships",
            "certifications",
            "certificates",
            "achievements",
            "awards"
        )
        heading_pattern = "|".join(re.escape(heading) for heading in all_headings)
        wanted_pattern = "|".join(re.escape(heading) for heading in headings)
        pattern = re.compile(
            rf"^\s*(?:{wanted_pattern})\s*:?\s*$",
            flags=re.IGNORECASE | re.MULTILINE
        )
        match = pattern.search(resume_text)

        if not match:
            return []

        rest = resume_text[match.end():]
        next_heading = re.search(
            rf"^\s*(?:{heading_pattern})\s*:?\s*$",
            rest,
            flags=re.IGNORECASE | re.MULTILINE
        )

        if next_heading:
            rest = rest[:next_heading.start()]

        return [
            re.sub(r"^[\-*•\d.)\s]+", "", line).strip()
            for line in rest.splitlines()
            if line.strip()
        ]

    def _fallback_from_resume_text(self, resume_text: str) -> dict:
        lines = [
            line.strip()
            for line in resume_text.splitlines()
            if line.strip()
        ]
        data = self._empty_resume_data()

        for line in lines[:8]:
            if (
                len(line.split()) <= 5
                and "@" not in line
                and not re.search(r"\d{5,}", line)
                and not line.lower().startswith(("resume", "cv"))
            ):
                data["name"] = line
                break

        summary_lines = self._section_lines(resume_text, ("summary", "objective"))
        if summary_lines:
            filtered_summary = [
                line
                for line in summary_lines
                if "@" not in line and not re.search(r"\+?\d[\d\s-]{7,}", line)
            ]
            data["summary"] = " ".join(filtered_summary[:3])

        skill_lines = self._section_lines(
            resume_text,
            ("skills", "technical skills")
        )
        skills = []
        blocked_skill_terms = (
            "linkedin",
            "github",
            "kaggle",
            "medium",
            "college",
            "university",
            "cgpa",
            "bachelor",
            "technology",
            "present",
            "uttarakhand",
            "roorkee",
            "coursework"
        )

        for line in skill_lines:
            line_lower = line.lower()

            if any(term in line_lower for term in blocked_skill_terms):
                continue

            skills.extend(
                part.strip()
                for part in re.split(r"[,|;/]", line)
                if part.strip()
            )

        section_skills = []

        for skill in skills:
            skill_lower = skill.lower()

            if any(term in skill_lower for term in blocked_skill_terms):
                continue

            if re.search(r"\b\d{4}\b", skill):
                continue

            if re.fullmatch(r"[\d.\-/]+", skill):
                continue

            if len(skill.split()) > 4:
                continue

            skill = re.sub(
                r"^(platforms?|soft skills?|programming languages?)\s+",
                "",
                skill,
                flags=re.IGNORECASE
            ).strip()

            if not skill:
                continue

            section_skills.append(skill)

        existing = set()
        for skill in section_skills:
            if skill.lower() not in existing:
                data["skills"].append(skill)
                existing.add(skill.lower())

        data["skills"] = data["skills"][:30]
        data["education"] = self._section_lines(resume_text, ("education",))[:10]
        data["projects"] = self._section_lines(resume_text, ("projects", "project"))[:12]
        data["internship"] = self._section_lines(
            resume_text,
            ("internship", "internships", "experience")
        )[:12]
        data["certifications"] = self._section_lines(
            resume_text,
            ("certifications", "certificates")
        )[:10]
        data["achievements"] = self._section_lines(
            resume_text,
            ("achievements", "awards")
        )[:10]

        return data

    def analyze_resume(self, resume_text: str):

        prompt = build_resume_prompt(resume_text)

        try:
            response = self.llm.invoke(prompt)
            content = str(getattr(response, "content", response))
            data = self._load_json_content(content)
            data = self._merge_resume_data(
                data,
                self._fallback_from_resume_text(resume_text)
            )

            if not self._has_resume_data(data):
                return self._fallback_from_resume_text(resume_text)

            return data

        except Exception as e:

            print("Resume Parsing Error:", e)
            if "response" in locals():
                print("Raw Resume LLM Response:", getattr(response, "content", response))

            return self._fallback_from_resume_text(resume_text)

    def extract_resume_data(self, resume_text: str):
        return self.analyze_resume(resume_text)
