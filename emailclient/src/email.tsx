interface Email {
    id: number;
    subject: string;
    content: string;
    email_to: { accounts: { name: string; address: string }[] } | null;
    email_from: { name: string; address: string };
    cc: { accounts: { name: string; address: string }[] } | null;
    bcc: { accounts: { name: string; address: string }[] } | null;
    email_date: string;
}

export default Email;
