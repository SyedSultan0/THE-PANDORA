export default function SessionStart({ candidate, onCandidateChange, onStart }) {
  const handleChange = (field) => (event) => {
    onCandidateChange({ ...candidate, [field]: event.target.value });
  };

  return (
    <section className="card session-start">
      <h2>Start a New Interview</h2>
      <p className="card-hint">Enter your details to begin a technical interview.</p>

      <div className="form-field">
        <label htmlFor="candidate-name">Name</label>
        <input
          id="candidate-name"
          type="text"
          value={candidate.name}
          onChange={handleChange("name")}
          placeholder="e.g. Sarah Johnson"
          autoComplete="name"
        />
      </div>

      <div className="form-field">
        <label htmlFor="candidate-role">Job Role</label>
        <input
          id="candidate-role"
          type="text"
          value={candidate.jobRole}
          onChange={handleChange("jobRole")}
          placeholder="e.g. Data Engineer"
        />
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
        />
      </div>

      <button type="button" className="btn btn-primary" onClick={onStart}>
        Start Interview
      </button>
    </section>
  );
}