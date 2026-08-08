import { useState } from "react";

export default function SessionStart({ candidate, onCandidateChange, onStart, isStarting }) {
  const [errors, setErrors] = useState({});

  const handleChange = (field) => (event) => {
    onCandidateChange({ ...candidate, [field]: event.target.value });
    // Clear the field error as soon as the user starts typing.
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleStart = () => {
    const nextErrors = {};
    if (!candidate.name.trim()) {
      nextErrors.name = "Name is required.";
    }
    if (!candidate.jobRole.trim()) {
      nextErrors.jobRole = "Job role is required.";
    }
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }
    setErrors({});
    onStart();
  };

  return (
    <section className="card session-start">
      <h2>Start a New Interview</h2>
      <p className="card-hint">Enter your details to begin a technical interview.</p>

      <div className={`form-field${errors.name ? " has-error" : ""}`}>
        <label htmlFor="candidate-name">
          Name <span className="required-mark" aria-hidden="true">*</span>
        </label>
        <input
          id="candidate-name"
          type="text"
          value={candidate.name}
          onChange={handleChange("name")}
          placeholder="e.g. Sarah Johnson"
          autoComplete="name"
          disabled={isStarting}
          aria-invalid={Boolean(errors.name)}
          aria-describedby={errors.name ? "candidate-name-error" : undefined}
        />
        {errors.name && (
          <p className="field-error" id="candidate-name-error" role="alert">
            {errors.name}
          </p>
        )}
      </div>

      <div className={`form-field${errors.jobRole ? " has-error" : ""}`}>
        <label htmlFor="candidate-role">
          Job Role <span className="required-mark" aria-hidden="true">*</span>
        </label>
        <input
          id="candidate-role"
          type="text"
          value={candidate.jobRole}
          onChange={handleChange("jobRole")}
          placeholder="e.g. Data Engineer"
          disabled={isStarting}
          aria-invalid={Boolean(errors.jobRole)}
          aria-describedby={errors.jobRole ? "candidate-role-error" : undefined}
        />
        {errors.jobRole && (
          <p className="field-error" id="candidate-role-error" role="alert">
            {errors.jobRole}
          </p>
        )}
      </div>

      <div className="form-field">
        <label htmlFor="candidate-experience">Years of Experience</label>
        <input
          id="candidate-experience"
          type="number"
          min="0"
          value={candidate.yearsExperience}
          onChange={handleChange("yearsExperience")}
          placeholder="e.g. 5"
          disabled={isStarting}
        />
      </div>

      <button type="button" className="btn btn-primary" onClick={handleStart} disabled={isStarting}>
        {isStarting ? "Starting..." : "Start Interview"}
      </button>
    </section>
  );
}