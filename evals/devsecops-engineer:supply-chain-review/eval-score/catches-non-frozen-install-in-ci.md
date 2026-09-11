PASS

The target explicitly identifies both drift points (CI's `npm install` and Dockerfile's `npm install --production`), explains that `npm ci` is the frozen-mode command that fails on lockfile/resolution disagreement while `npm install` silently proceeds, and echoes the skill's own framing verbatim ("A lockfile that nothing installs from in frozen mode is decoration"), going beyond merely noting the lockfile exists.
