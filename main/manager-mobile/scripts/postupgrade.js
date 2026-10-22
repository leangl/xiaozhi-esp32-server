// # Running `pnpm upgrade` updates uni-app dependencies
// # Upgrading also adds unused dependencies; remove them to reduce package size
// # Run the command below

const { exec } = require('node:child_process')

// Define the command to execute
const dependencies = [
  '@dcloudio/uni-app-harmony',
  // TODO: Remove or comment out mini-program platforms you do not need
  '@dcloudio/uni-mp-alipay',
  '@dcloudio/uni-mp-baidu',
  '@dcloudio/uni-mp-jd',
  '@dcloudio/uni-mp-kuaishou',
  '@dcloudio/uni-mp-lark',
  '@dcloudio/uni-mp-qq',
  '@dcloudio/uni-mp-toutiao',
  '@dcloudio/uni-mp-xhs',
  '@dcloudio/uni-quickapp-webview',
  // Comment out the following entries for the i18n template
  'vue-i18n',
]

// Execute the command with exec
exec(`pnpm un ${dependencies.join(' ')}`, (error, stdout, stderr) => {
  if (error) {
    // Print execution errors
    console.error(`Command execution failed: ${error}`)
    return
  }
  // Print standard output
  console.log(`stdout: ${stdout}`)
  // Also print standard error
  console.error(`stderr: ${stderr}`)
})
