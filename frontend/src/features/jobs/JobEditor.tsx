import { useState } from 'react';

export default function JobEditor() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [stageOrder, setStageOrder] = useState('online_assessment,coding_assessment,voice_interview');
  const [recommendationThreshold, setRecommendationThreshold] = useState('80');
  const [error, setError] = useState('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    if (!title.trim() || !description.trim()) {
      setError('Title and description are required.');
      return;
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Title
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
      </label>
      <label>
        Description
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>
      <label>
        Stage order
        <input
          aria-label="Stage order"
          value={stageOrder}
          onChange={(e) => setStageOrder(e.target.value)}
        />
      </label>
      <label>
        Recommendation threshold
        <input
          aria-label="Recommendation threshold"
          type="number"
          min="0"
          max="100"
          value={recommendationThreshold}
          onChange={(e) => setRecommendationThreshold(e.target.value)}
        />
      </label>
      {error ? <p role="alert">{error}</p> : null}
      <button type="submit">Save job</button>
    </form>
  );
}
