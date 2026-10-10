export interface Letter {
  address: string;
  recipient: string;
  body: string;
}

export interface PostalQueue {
  queue(letter: Letter): Promise<void>;
}
