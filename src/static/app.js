document.addEventListener('DOMContentLoaded', () => {
    const btnStep = document.getElementById('btn-step');
    const btnReset = document.getElementById('btn-reset');
    const explanationBox = document.getElementById('explanation-box');
    const statusText = document.getElementById('status-text');
    const timeline = document.getElementById('timeline');
    const scheduledList = document.getElementById('scheduled-list');
    const eligibleList = document.getElementById('eligible-list');

    let maxTime = 1; // Track the maximum time to scale the Gantt chart

    // Initialize
    resetState();

    btnStep.addEventListener('click', stepState);
    btnReset.addEventListener('click', resetState);

    async function stepState() {
        btnStep.disabled = true;
        try {
            const response = await fetch('/step', { method: 'POST' });
            const data = await response.json();
            updateUI(data);
        } catch (error) {
            console.error("Error stepping:", error);
            explanationBox.innerText = "Error communicating with server.";
        }
        btnStep.disabled = false;
    }

    async function resetState() {
        btnStep.disabled = true;
        btnReset.disabled = true;
        try {
            const response = await fetch('/reset', { method: 'POST' });
            const data = await response.json();
            updateUI(data);
        } catch (error) {
            console.error("Error resetting:", error);
            explanationBox.innerText = "Error communicating with server.";
        }
        btnStep.disabled = false;
        btnReset.disabled = false;
    }

    function updateUI(data) {
        if (data.done) {
            explanationBox.innerText = "Project scheduling is complete!";
            statusText.innerText = "Finished";
            statusText.style.color = "var(--success)";
            btnStep.disabled = true;
            return;
        }

        explanationBox.innerText = data.explanation;
        statusText.innerText = data.status;

        // Render tags
        scheduledList.innerHTML = '';
        data.scheduled.forEach(act => {
            const span = document.createElement('span');
            span.className = 'tag scheduled';
            span.innerText = `Act ${act}`;
            scheduledList.appendChild(span);
        });

        eligibleList.innerHTML = '';
        data.eligible.forEach(act => {
            const span = document.createElement('span');
            span.className = 'tag eligible';
            span.innerText = `Act ${act}`;
            eligibleList.appendChild(span);
        });

        // Update Timeline
        renderTimeline(data);
    }

    function renderTimeline(data) {
        timeline.innerHTML = '';
        
        // Find max finish time to calculate percentages
        let currentMax = 1;
        data.scheduled.forEach(act => {
            if (data.finish_times[act] > currentMax) {
                currentMax = data.finish_times[act];
            }
        });
        // Give a little buffer
        maxTime = Math.max(maxTime, currentMax + 5);

        // Render each scheduled activity
        data.activities.forEach(act => {
            if (!data.scheduled.includes(act)) return;

            const start = data.start_times[act];
            const finish = data.finish_times[act];
            const dur = data.durations[act];

            const row = document.createElement('div');
            row.className = 'timeline-row';

            const label = document.createElement('div');
            label.className = 'timeline-label';
            label.innerText = `Act ${act}`;

            const track = document.createElement('div');
            track.className = 'timeline-track';

            const bar = document.createElement('div');
            bar.className = 'gantt-bar';
            
            // Calculate position and width
            const leftPct = (start / maxTime) * 100;
            const widthPct = (dur / maxTime) * 100;
            
            bar.style.left = `${leftPct}%`;
            // Minimum width to show zero duration dummy tasks
            bar.style.width = dur === 0 ? '4px' : `${widthPct}%`;
            if(dur === 0) {
                bar.style.background = 'gray';
            }

            if (dur > 0) {
                bar.innerText = `[${start}-${finish}]`;
            }

            track.appendChild(bar);
            row.appendChild(label);
            row.appendChild(track);
            timeline.appendChild(row);
        });
    }
});
