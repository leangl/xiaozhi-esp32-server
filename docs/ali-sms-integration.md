# Alibaba Cloud SMS integration

Sign in to the Alibaba Cloud console and open [SMS Service](https://dysms.console.aliyun.com/overview).

## Step 1: Add a signature

Open **Domestic Messages > Signature Management** and click **Add Signature**:

![Add an SMS signature](images/alisms/sms-01.png)

Enter your approved organization/app/trademark signature, choose the appropriate usage and qualification information, describe the use case, provide supporting documents where required, and submit:

![Complete and submit the signature form](images/alisms/sms-02.png)

Put the approved signature text in the management console parameter `aliyun.sms.sign_name`.

The original guide warns that carrier registration can take seven business days and sending will fail before approval. Wait for successful registration before continuing; provider processing times may vary.

## Step 2: Add a template

Open **Domestic Messages > Template Management**. Add an approved verification-code template or use the available approved one, then copy its **Template CODE** (the highlighted `SMS_...` value):

![Find the verification-code template code](images/alisms/sms-11.png)

Set `aliyun.sms.sms_code_template_code` to that code.

## Step 3: Create an SMS account and grant permissions

Open [RAM Access Control](https://ram.console.aliyun.com/overview?activeTab=overview).

In **Identity Management > Users**, click **Create User**:

![Create a RAM user](images/alisms/sms-21.png)

Enter a login name and display name. The screenshot uses an SMS-specific user and enables permanent **AccessKey** access, leaving console access unchecked. Confirm creation:

![Configure user identity and AccessKey access](images/alisms/sms-22.png)

Copy the **AccessKey ID** and **AccessKey Secret** before closing the result page; the secret is not available again there:

![Copy the AccessKey credentials](images/alisms/sms-23.png)

Return to the user list, find the SMS user you created, and click **Add Permissions**:

![Add permissions to the SMS user](images/alisms/sms-24.png)

Confirm that the authorization principal is that same SMS user. Search for `sms`. The original screenshot selects the existing system policies `AliyunDysmsFullAccess` and `AliyunDysmsReadOnlyAccess`, then clicks **Confirm New Authorization**:

![Select the original SMS policies and confirm authorization](images/alisms/sms-25.png)

This describes the screenshot's existing permission choice without changing it; the full-access policy is broad and needs a separate least-privilege review.

Set `aliyun.sms.access_key_id` and `aliyun.sms.access_key_secret` to the generated credentials in the management console.

## Step 4: Enable mobile registration

Search for `sms` in **Parameter Management**. Confirm the access-key ID, secret, signature, and template-code parameters are populated. The screenshot also shows the per-number daily message limit; do not copy its example credentials.

![Review the configured SMS parameters](images/alisms/sms-31.png)

Set `server.allow_user_register` to `true` to allow non-administrator registration. Set `server.enable_mobile_register` to `true` to enable mobile registration.

![Enable mobile registration](images/alisms/sms-32.png)

The last historical screenshot displays `system.enable_mobile_register`, while the original prose uses `server.enable_mobile_register`. Verify the parameter exposed by your installed version; this translation preserves both references rather than silently renaming a configuration key.
