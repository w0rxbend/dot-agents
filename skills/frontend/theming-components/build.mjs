import StyleDictionary from 'style-dictionary';
import config from './config.js';

// Style Dictionary reads sources at the dictionary level. Build each platform
// separately so its theme overrides apply to its own outputs.
for (const [name, platform] of Object.entries(config.platforms)) {
  const { source = config.source, ...settings } = platform;
  const dictionary = new StyleDictionary({
    ...config,
    source,
    platforms: { [name]: settings },
  });
  await dictionary.buildAllPlatforms();
}
